"""
Copyright (c) 2014, Samsung Electronics Co.,Ltd.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of Samsung Electronics Co.,Ltd..
"""

"""
cuda4py - CUDA cffi bindings and helper classes.
URL: https://github.com/ajkxyz/cuda4py
Original author: Alexey Kazantsev <a.kazantsev@samsung.com>
"""

"""
Tests some of the api in cuda4py.curand package.
"""
import cuda4py as cu
import cuda4py.curand as curand
import gc
import logging
import numpy
import os
import unittest


class Test(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.old_env = os.environ.get("CUDA_DEVICE")
        if self.old_env is None:
            os.environ["CUDA_DEVICE"] = "0"
        self.ctx = cu.Devices().create_some_context()
        self.path = os.path.dirname(__file__)
        if not len(self.path):
            self.path = "."

    def tearDown(self):
        if self.old_env is None:
            del os.environ["CUDA_DEVICE"]
        else:
            os.environ["CUDA_DEVICE"] = self.old_env
        del self.old_env
        del self.ctx
        gc.collect()

    def test_constants(self):
        self.assertEqual(curand.CURAND_STATUS_SUCCESS, 0)
        self.assertEqual(curand.CURAND_STATUS_VERSION_MISMATCH, 100)
        self.assertEqual(curand.CURAND_STATUS_NOT_INITIALIZED, 101)
        self.assertEqual(curand.CURAND_STATUS_ALLOCATION_FAILED, 102)
        self.assertEqual(curand.CURAND_STATUS_TYPE_ERROR, 103)
        self.assertEqual(curand.CURAND_STATUS_OUT_OF_RANGE, 104)
        self.assertEqual(curand.CURAND_STATUS_LENGTH_NOT_MULTIPLE, 105)
        self.assertEqual(curand.CURAND_STATUS_DOUBLE_PRECISION_REQUIRED, 106)
        self.assertEqual(curand.CURAND_STATUS_LAUNCH_FAILURE, 201)
        self.assertEqual(curand.CURAND_STATUS_PREEXISTING_FAILURE, 202)
        self.assertEqual(curand.CURAND_STATUS_INITIALIZATION_FAILED, 203)
        self.assertEqual(curand.CURAND_STATUS_ARCH_MISMATCH, 204)
        self.assertEqual(curand.CURAND_STATUS_INTERNAL_ERROR, 999)

        self.assertEqual(curand.CURAND_RNG_TEST, 0)
        self.assertEqual(curand.CURAND_RNG_PSEUDO_DEFAULT, 100)
        self.assertEqual(curand.CURAND_RNG_PSEUDO_XORWOW, 101)
        self.assertEqual(curand.CURAND_RNG_PSEUDO_MRG32K3A, 121)
        self.assertEqual(curand.CURAND_RNG_PSEUDO_MTGP32, 141)
        self.assertEqual(curand.CURAND_RNG_PSEUDO_MT19937, 142)
        self.assertEqual(curand.CURAND_RNG_PSEUDO_PHILOX4_32_10, 161)
        self.assertEqual(curand.CURAND_RNG_QUASI_DEFAULT, 200)
        self.assertEqual(curand.CURAND_RNG_QUASI_SOBOL32, 201)
        self.assertEqual(curand.CURAND_RNG_QUASI_SCRAMBLED_SOBOL32, 202)
        self.assertEqual(curand.CURAND_RNG_QUASI_SOBOL64, 203)
        self.assertEqual(curand.CURAND_RNG_QUASI_SCRAMBLED_SOBOL64, 204)

        self.assertEqual(curand.CURAND_ORDERING_PSEUDO_BEST, 100)
        self.assertEqual(curand.CURAND_ORDERING_PSEUDO_DEFAULT, 101)
        self.assertEqual(curand.CURAND_ORDERING_PSEUDO_SEEDED, 102)
        self.assertEqual(curand.CURAND_ORDERING_QUASI_DEFAULT, 201)

    def test_errors(self):
        idx = cu.CU.ERRORS[curand.CURAND_STATUS_NOT_INITIALIZED].find(" | ")
        self.assertGreater(idx, 0)

    def test_create(self):
        rng = curand.CURAND(self.ctx)
        del rng

    def test_properties(self):
        rng = curand.CURAND(self.ctx)
        self.assertEqual(rng.rng_type, curand.CURAND_RNG_PSEUDO_DEFAULT)

        # version
        ver = rng.version
        logging.debug("cuRAND version is %d", ver)
        self.assertTrue(ver == int(ver))

        # ordering, seed, offset, dimensions
        self.assertEqual(rng.ordering, 0)
        rng.ordering = curand.CURAND_ORDERING_PSEUDO_DEFAULT

        try:
            rng.dimensions = 64
        except cu.CUDARuntimeError:
            pass
        self.assertEqual(rng.dimensions, 0)

        self.assertEqual(rng.ordering, curand.CURAND_ORDERING_PSEUDO_DEFAULT)
        self.assertEqual(rng.seed, 0)
        self.assertEqual(rng.offset, 0)
        rng.seed = 123
        self.assertEqual(rng.seed, 123)
        self.assertEqual(rng.offset, 0)
        rng.offset = 4096
        self.assertEqual(rng.seed, 123)
        self.assertEqual(rng.offset, 4096)
        rng.seed = 12345.1
        rng.offset = 8192.3
        self.assertEqual(rng.seed, 12345)
        self.assertEqual(rng.offset, 8192)
        self.assertEqual(rng.ordering, curand.CURAND_ORDERING_PSEUDO_DEFAULT)

        rng = curand.CURAND(self.ctx, curand.CURAND_RNG_QUASI_DEFAULT)
        rng.dimensions = 64
        self.assertEqual(rng.dimensions, 64)
        self.assertEqual(rng.rng_type, curand.CURAND_RNG_QUASI_DEFAULT)
        self.assertEqual(rng.ordering, 0)
        self.assertEqual(rng.seed, 0)
        self.assertEqual(rng.offset, 0)

    def test_generate(self):
        self._test_generate(self.ctx)  # device version
        self._test_generate(None)  # host version

    def _test_generate(self, ctx):
        rng = curand.CURAND(ctx)
        rng.seed = 123
        a = numpy.zeros(65536, dtype=numpy.int32)
        a_buf = cu.MemAlloc(ctx, a) if ctx is not None else numpy.zeros_like(a)
        rng.generate32(a_buf, a.size)
        if ctx is not None:
            a_buf.to_host(a)
        else:
            a[:] = a_buf[:]
        self.assertGreater(numpy.count_nonzero(a), a.size - a.size // 512)

        # Check that seed matters
        rng = curand.CURAND(ctx)
        rng.seed = 123
        if ctx is not None:
            a_buf.memset32_async()
        else:
            a_buf[:] = 0
        rng.generate32(a_buf, a.size)
        b = numpy.zeros_like(a)
        if ctx is not None:
            a_buf.to_host(b)
        else:
            b[:] = a_buf[:]
        self.assertEqual(numpy.count_nonzero(a - b), 0)

        rng = curand.CURAND(ctx)
        rng.seed = 456
        if ctx is not None:
            a_buf.memset32_async()
        else:
            a_buf[:] = 0
        rng.generate32(a_buf, a.size)
        if ctx is not None:
            a_buf.to_host(b)
        else:
            b[:] = a_buf[:]
        self.assertGreater(numpy.count_nonzero(a - b), a.size - a.size // 512)

        # Check that result will be the same when the size is not passed
        rng = curand.CURAND(ctx)
        rng.seed = 123
        if ctx is not None:
            a_buf.memset32_async()
        else:
            a_buf[:] = 0
        rng.generate32(a_buf)
        b = numpy.zeros_like(a)
        if ctx is not None:
            a_buf.to_host(b)
        else:
            b[:] = a_buf[:]
        self.assertEqual(numpy.count_nonzero(a - b), 0)

        # Check 64-bit version
        rng = curand.CURAND(ctx, curand.CURAND_RNG_QUASI_SOBOL64)
        try:
            rng.seed = 123
            self.assertTrue(
                False, "CURAND_RNG_QUASI_SOBOL64 should not support seed")
        except cu.CUDARuntimeError:
            pass
        rng.dimensions = 64
        if ctx is not None:
            a_buf.memset32_async()
        else:
            a_buf[:] = 0
        try:
            rng.generate32(a_buf, a.size)
            self.assertTrue(
                False,
                "CURAND_RNG_QUASI_SOBOL64 should not support generate32")
        except cu.CUDARuntimeError:
            pass
        a64 = numpy.zeros(a.size // 2, dtype=numpy.int64)
        rng.generate64(a_buf, a64.size)
        if ctx is not None:
            a_buf.to_host(a64)
        else:
            a64[:] = a_buf.view(numpy.int64)[:]
        self.assertGreater(numpy.count_nonzero(a64),
                           a64.size - a64.size // 256)

        # Check that result will be the same when the size is not passed
        rng = curand.CURAND(ctx, curand.CURAND_RNG_QUASI_SOBOL64)
        rng.dimensions = 64
        if ctx is not None:
            a_buf.memset32_async()
        else:
            a_buf[:] = 0
        rng.generate64(a_buf)
        b64 = numpy.zeros_like(a64)
        if ctx is not None:
            a_buf.to_host(b64)
        else:
            b64[:] = a_buf.view(numpy.int64)[:]
        self.assertEqual(numpy.count_nonzero(a64 - b64), 0)

    def _test_generate_uniform(self, ctx, dtype, func, pass_size):
        a = numpy.zeros(65536, dtype=dtype)
        a_buf = cu.MemAlloc(ctx, a) if ctx is not None else numpy.zeros_like(a)
        if pass_size:
            func(a_buf, a.size)
        else:
            func(a_buf)
        if ctx is not None:
            a_buf.to_host(a)
        else:
            a[:] = a_buf[:]
        # Simple test for correctness
        N = 20
        counts = [0 for _i in range(N)]
        for x in a:
            counts[int(x * N)] += 1
        for c in counts:
            self.assertLess(abs(c - a.size // N), a.size // N // 8)
        return a

    def test_generate_uniform(self):
        for ctx in (self.ctx, None):
            res = []
            for pass_size in (True, False):
                rng = curand.CURAND(ctx)
                rng.seed = 123
                res.append(self._test_generate_uniform(
                    ctx, numpy.float32, rng.generate_uniform, pass_size))
                res.append(self._test_generate_uniform(
                    ctx, numpy.float64, rng.generate_uniform_double,
                    pass_size))
            for i in range(2):
                self.assertEqual(numpy.count_nonzero(res[i] - res[i + 2]), 0)

    def _test_generate_normal(self, ctx, dtype, func, pass_size):
        a = numpy.zeros(65536, dtype=dtype)
        a_buf = cu.MemAlloc(ctx, a) if ctx is not None else numpy.zeros_like(a)
        mean = 1.0
        stddev = 2.0
        if pass_size:
            func(a_buf, a.size)
            func(a_buf, a.size, mean, stddev)
        else:
            func(a_buf)
            func(a_buf, mean=mean, stddev=stddev)
        if ctx is not None:
            a_buf.to_host(a)
        else:
            a[:] = a_buf[:]
        # TODO(a.kazantsev): add better test for correctness.
        self.assertGreater(numpy.count_nonzero(a), a.size - a.size // 512)
        return a

    def test_generate_normal(self):
        for ctx in (self.ctx, None):
            res = []
            for pass_size in (True, False):
                rng = curand.CURAND(ctx)
                rng.seed = 123
                a = self._test_generate_normal(
                    ctx, numpy.float32, rng.generate_normal, pass_size)
                a64 = self._test_generate_normal(
                    ctx, numpy.float64, rng.generate_normal_double, pass_size)
                rng = curand.CURAND(ctx)
                rng.seed = 123
                b = self._test_generate_normal(
                    ctx, numpy.float32, rng.generate_log_normal, pass_size)
                b64 = self._test_generate_normal(
                    ctx, numpy.float64, rng.generate_log_normal_double,
                    pass_size)
                self.assertGreater(numpy.count_nonzero(a - b),
                                   a.size - a.size // 512)
                self.assertGreater(
                    numpy.count_nonzero(a64 - b64), a.size - a.size // 512)
                res.extend((a, a64, b, b64))
            for i in range(4):
                self.assertEqual(numpy.count_nonzero(res[i] - res[i + 4]), 0)

    def test_poisson(self):
        for ctx in (self.ctx, None):
            res = []
            for pass_size in (True, False):
                rng = curand.CURAND(ctx)
                rng.seed = 123
                a = numpy.zeros(65536, dtype=numpy.uint32)
                a_buf = (cu.MemAlloc(ctx, a) if ctx is not None
                         else numpy.zeros_like(a))
                if pass_size:
                    rng.generate_poisson(a_buf, a.size)
                    rng.generate_poisson(a_buf, a.size, 1.0)
                else:
                    rng.generate_poisson(a_buf)
                    rng.generate_poisson(a_buf, lam=1.0)
                if ctx is not None:
                    a_buf.to_host(a)
                else:
                    a[:] = a_buf[:]
                # TODO(a.kazantsev): add better test for correctness.
                self.assertGreater(numpy.count_nonzero(a), a.size // 2)
                res.append(a)
            for i in range(1):
                self.assertEqual(numpy.count_nonzero(res[i] - res[i + 1]), 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
