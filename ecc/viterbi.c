#ifdef __ARM_NEON
#include <arm_neon.h>
#endif
#include <assert.h>
#include <string.h>
#ifdef __ARM_FEATURE_SIMD32
#include "math/arm_simd32.h"
#endif
#include "protocol/cadu.h"
#include "utils.h"
#include "viterbi.h"

#define NEXT_DEPTH(x) (((x) + 1) % LEN(_prev))
#define PREV_DEPTH(x) (((x) - 1 + LEN(_prev)) % LEN(_prev))
#define BETTER_METRIC(x, y) ((x) > (y))    /* Higher metric is better */
#define POLY_TOP_BITS ((G1 >> (K-1) & 1) << 1 | (G2 >> (K-1)))
#define TWIN_METRIC(metric, x, y) (\
	POLY_TOP_BITS == 0x0 ? (metric) : \
	POLY_TOP_BITS == 0x1 ? (metric)-2*(x) : \
	POLY_TOP_BITS == 0x2 ? (metric)-2*(y) : (-metric))

static int  parity(uint32_t word);
static int  metric(int x, int y, int coding);
static void update_metrics(int8_t x, int8_t y, int depth);
static void backtrace(uint8_t *out, uint8_t state, int depth, int bitskip, int bitcount);

/* Backend arrays accessed via pointers defined below */
static int16_t _raw_metrics[NUM_STATES];
static int16_t _raw_next_metrics[NUM_STATES];

static uint8_t _output_lut[NUM_STATES];         /* Encoder output given a state */
static int16_t *_metrics, *_next_metrics;       /* Pointers to current and previous metrics for each state */
static uint8_t _prev[MEM_DEPTH][NUM_STATES/2];  /* Trellis diagram (pairs of states share the same predecessor) */
static int _depth;                              /* Current memory depth in the trellis array */

/* Static functions {{{ */
static int
parity(uint32_t word)
{
	/* From bit twiddling hacks */
	word ^= (word >> 1);
	word ^= (word >> 2);
	word = (word & 0x11111111) * 0x11111111;
	return (word >> 28) & 0x1;
}

uint32_t
conv_encode_u32(uint64_t *output, uint32_t state, uint32_t data)
{
	int i;
	uint8_t tmp;

	*output = 0;
	for (i=31; i>=0; i--) {
		/* Compute new state */
		state = ((state >> 1) | ((data >> i) << (K-1))) & (NUM_STATES - 1);

		/* Compute output */
		tmp = parity(state & G1) << 1 | parity(state & G2);
		*output |= (uint64_t)tmp << (i<<1);
	}

	return state;
}

void
viterbi_init()
{
	int i, input, state, next_state, output;

	/* Precompute the output given a state and an input */
	for (state=0; state<NUM_STATES; state++) {
		input = 0;      /* Output for input=1 is _output_lut[state] ^ POLY_TOP_BITS */
		next_state = (state >> 1) | (input << (K-1));
		output = parity(next_state & G1) << 1 | parity(next_state & G2);

		/* The ARM SIMD32 optimized algorithm stores the local metrics in a
		 * single uint32_t, so the output computed here is used as a shift value
		 * rather than an index in an array. For this reason, [0, 1, 2, 3]
		 * indices become [0, 8, 16, 24] shifts */
#if defined(__ARM_FEATURE_SIMD32) && !defined(__ARM_NEON)
		_output_lut[state] = output << 3;
#else
		_output_lut[state] = output;
#endif
	}

	/* Initialize current Viterbi depth */
	_depth = 0;

	/* Initialize state metrics in the backtrack memory */
	for (i=0; i<NUM_STATES; i++) {
		_raw_metrics[i] = 0;
	}

	/* Bind metric arrays to the Viterbi struct */
	_metrics = _raw_metrics;
	_next_metrics = _raw_next_metrics;
}


int
viterbi_decode(uint8_t *restrict out, int8_t *restrict soft_cadu, int bytecount)
{
  // size of soft_cadu 1024 * 8 * 2
    FILE *f = fopen("soft_cadu.txt", "wb");
    for (int i  = 0; i < bytecount * 2; i++) { 
      fprintf(f, "%c", soft_cadu[i]);
    }
    fclose(f);


    char command[256];
    snprintf(command, sizeof(command), "python3 /home/sammy/shit/meteor_decode/viterbi_interface.py %d", bytecount);
    system(command);
    /* printf("Finish"); */


    FILE *file;

    // Open the file for reading
    file = fopen("viterbi.txt", "r");
    if (file == NULL) {
        perror("Error opening file");
        return 1;
    }
    int ind = 0;
    uint8_t value;

    /* printf("here"); */
    while (fscanf(file, "%c", &value) == 1 && ind < bytecount) {
        out[ind++] = (uint8_t)value;
        /* printf("int: %d", value); */
    }
    fclose(file);

  
  /* Py_Initialize(); */
  /* char* path = "/home/sammy/shit/meteor_decode"; */
  /* wchar_t* wpath = Py_DecodeLocale(path, NULL); */
  /* if (wpath != NULL) { */
  /*     PySys_SetPath(wpath); */
  /*     PyMem_RawFree(wpath); */
  /* } */

  /* PyObject *pName = PyUnicode_DecodeFSDefault("viterbi_interface"); */
  /* PyObject *pModule = PyImport_Import(pName); */
  /* Py_XDECREF(pName); */
  /* if (pModule != NULL) { */
  /*     PyObject *pFunc = PyObject_GetAttrString(pModule, "viterbi"); */
  /*     if (pFunc != NULL && PyCallable_Check(pFunc)) { */
  /*         PyObject *pArgs = PyTuple_Pack(2, PyLong_FromLong(bytecount), */ 
  /*             PyByteArray_FromStringAndSize((char *)soft_cadu, bytecount)); */
  /*         PyObject *pValue = PyObject_CallObject(pFunc, pArgs); */
  /*         if (pValue != NULL) { */
  /*             PyByteArrayObject *result_array = (PyByteArrayObject *)pValue; */
  /*             int output_length = PyByteArray_GET_SIZE(result_array); */
  /*             char *buffer = PyByteArray_AsString((PyObject *)result_array); */
  /*             for (int i = 0; i < output_length; ++i) { */
  /*                 printf("OUTPUT: length: %d, i: %d", output_length, i); */
  /*                 out[i] = (uint8_t)buffer[i]; */
  /*             } */
  /*             Py_XDECREF(pValue); */
  /*         } else { */
  /*             PyErr_Print(); */
  /*         } */
  /*         Py_XDECREF(pArgs); */
  /*         Py_XDECREF(pFunc); */
  /*     } else { */
  /*         PyErr_Print(); */
  /*     } */

  /*     Py_XDECREF(pModule); */
  /* } else { */
  /*     PyErr_Print(); */
  /* } */
  /* Py_Finalize(); */

  // Metric only for display -> return zero 
	return 0;
}


/* }}} */
