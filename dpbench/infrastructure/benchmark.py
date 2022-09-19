# Copyright 2021 ETH Zurich and the NPBench authors. All rights reserved.
# Copyright 2022 Intel Corp.
#
# SPDX-License-Identifier: BSD-3-Clause

import json
import pathlib
import warnings
from inspect import getmembers
from typing import Any, Dict

import numpy as np

import dpbench.infrastructure as dpbi
from dpbench.infrastructure import timeout_decorator as tout
from dpbench.infrastructure import timer

from .framework import Framework


def get_supported_implementation_postfixes():
    """Returns as a dictionary all the supported postfixes for filenames
    that implement a specific version of a benchmark.

    Returns:
        Dict: Key is the string providing the supported postfix and value is a
        string describing when to use the postfix.
    """
    parent_folder = pathlib.Path(__file__).parent.absolute()
    impl_postfix_json = parent_folder.joinpath(
        "..", "configs", "impl_postfix.json"
    )

    try:
        with open(impl_postfix_json) as json_file:
            return json.load(json_file)["impl_postfix"]
    except Exception as e:
        warnings.warn("impl_postfix.json file not found")
        raise (e)


class BenchmarkResults:
    """A helper class to store the results and timing from running a
    benchmark.
    """

    @property
    def benchmark(self):
        return self._bench

    @benchmark.setter
    def benchmark(self, bench):
        self._bench = bench

    @property
    def benchmark_name(self):
        """Returns the name of the benchmark.

        Returns:
            str: Name of the benchmark
        """
        return self._bench.bname

    @benchmark_name.setter
    def benchmark_name(self, bname):
        """Sets the name of the benchmark."""
        self._bench.bname = bname

    @property
    def benchmark_impl_postfix(self):
        """Returns the implementation type (postfix) of the benchmark.

        Returns:
            str: The implementation postfix for the benchmark's run
        """
        return self._impl_postfix

    @benchmark_impl_postfix.setter
    def benchmark_impl_postfix(self, impl_postfix: str):
        self._impl_postfix = impl_postfix

    @property
    def framework_name(self):
        """Returns the name of the Framework used to execute the benchmark

        Returns:
            str: The name of the Framework used for execution
        """
        return self._fmwrk.fname

    @property
    def framework(self):
        return self._fmwrk

    @framework.setter
    def framework(self, fmwrk):
        self._fmwrk = fmwrk

    @property
    def framework_version(self):
        """Returns the version of the Framework used to execute the benchmark

        Returns:
            str: The version of the Framework used for execution
        """
        return self._fmwrk.version()

    @property
    def setup_time(self):
        """Returns the time in nanoseconds used to setup the benchmark.

        Setting up a benchmark involves copying the data from NumPy to either
        other NumPy arrays or to a Framework-specific data container.

        Returns:
            float: Time in nanosecond spent on copying data from NumPy to
            Framework-specific data container.
        """
        return self._setup_time

    @setup_time.setter
    def setup_time(self, setup_time):
        self._setup_time = setup_time

    @property
    def warmup_time(self):
        return self._warmup_time

    @warmup_time.setter
    def warmup_time(self, warmup_time):
        self._warmup_time = warmup_time

    @property
    def teardown_time(self):
        """Returns the time in nanoseconds used to teardown the benchmark.

        Tearing down a benchmark involves copying the data from any
        Framework-specific data container to a NumPy array on the host system.

        Returns:
            float: Time in nanosecond spent on copying data from any
            Framework-specific data container to NumPy.
        """
        return self._teardown_time

    @teardown_time.setter
    def teardown_time(self, teardown_time):
        self._teardown_time = teardown_time

    @property
    def num_repeats(self):
        """Returns the number of repetitions of the main execution.

        Returns:
            int: Number of times the main program was executed.
        """
        return self._repeats

    @num_repeats.setter
    def num_repeats(self, repeats):
        self._repeats = repeats

    @property
    def preset(self):
        return self._preset

    @preset.setter
    def preset(self, preset):
        self._preset = preset

    @property
    def exec_times(self):
        """Returns an array of execution timings measured in nanoseconds

        Returns:
            numpy.ndarray: An array of execution times for each repetition of
            the main execution.
        """
        return self._exec_times

    @exec_times.setter
    def exec_times(self, exec_times):
        self._exec_times = exec_times
        self._exec_time_quartiles = np.percentile(exec_times, [25, 50, 75])

    @property
    def min_exec_time(self):
        """Minimum execution time for the benchmark out of the set of
        repetitions.

        Returns:
            float: Time in nanoseconds showing the fastest run out of all
            repeats.
        """
        return self._exec_times.min()

    @property
    def max_exec_time(self):
        """Maximum execution time for the benchmark out of the set of
        repetitions.

        Returns:
            float: Time in nanoseconds showing the slowest run out of all
            repeats.
        """
        return self._exec_times.max()

    @property
    def quartile25_exec_time(self):
        """25th quartile execution time for the benchmark out of the set of
        repetitions.

        Returns:
            float: Time in nanoseconds showing the 25th quartile run out of all
            repeats.
        """
        return self._exec_time_quartiles[0]

    @property
    def median_exec_time(self):
        """Median execution time for the benchmark out of the set of
        repetitions.

        Returns:
            float: Time in nanoseconds showing the median run out of all
            repeats.
        """
        return self._exec_time_quartiles[1]

    @property
    def quartile75_exec_time(self):
        """75th quartile execution time for the benchmark out of the set of
        repetitions.

        Returns:
            float: Time in nanoseconds showing the 75th quartile run out of all
            repeats.
        """
        return self._exec_time_quartiles[2]

    @property
    def results(self):
        """Returns as a list the output data from the benchmark.

        Returns:
            list: List of the output arguments generated by the benchmark.
        """
        return self._results

    @results.setter
    def results(self, results):
        self._results = results

    @property
    def validation_state(self):
        return self._validation_state

    @validation_state.setter
    def validation_state(self, validated):
        self._validation_state = validated

    @property
    def error_state(self):
        return self._error_state

    @error_state.setter
    def error_state(self, error_state):
        self._error_state = error_state

    @property
    def error_msg(self):
        return self._error_msg

    @error_msg.setter
    def error_msg(self, error_msg):
        self._error_msg = error_msg


class BenchmarkRunner:
    def __init__(self, bench, impl_postfix, preset, repeat, timeout):
        self.bench = bench
        self.preset = preset
        self.repeat = repeat
        self.timeout = timeout
        self.copied_args = dict()
        self.results = BenchmarkResults()
        self.impl_fn = self.bench.get_impl(impl_postfix)
        self.fmwrk = self.bench.get_framework(impl_postfix)

        self.results.benchmark = self.bench
        self.results.framework = self.fmwrk
        self.results.benchmark_impl_postfix = impl_postfix
        self.results.num_repeats = repeat
        self.results.preset = preset
        self.results.results = dict()

        if not self.impl_fn:
            self.results.error_state = -1
            self.results.error_msg = "No implementation"
        elif not self.fmwrk:
            self.results.error_state = -2
            self.results.error_msg = "No framework"
        else:
            self.results.error_state = 0
            self.results.error_msg = ""
            # Run setup step
            self._setup()
            # Execute the benchmark
            self._exec()

    def _setup(self):
        initialized_data = self.bench.get_data(preset=self.preset)
        array_args = self.bench.info["array_args"]

        with timer.timer() as t:
            for arg in array_args:
                npdata = initialized_data[arg]
                self.copied_args.update(
                    {arg: self.fmwrk.copy_to_func()(npdata)}
                )

        self.results.setup_time = t.get_elapsed_time()

    def _reset_output_args(self, inputs):
        try:
            output_args = self.bench.info["output_args"]
        except KeyError:
            warnings.warn(
                "No output args to reset as benchmarks has no array output."
            )
            return
        array_args = self.bench.info["array_args"]
        for arg in inputs.keys():
            if arg in output_args and arg in array_args:
                original_data = self.bench.get_data(preset=self.preset)[arg]
                inputs.update({arg: self.fmwrk.copy_to_func()(original_data)})

    def _exec(self):
        input_args = self.bench.info["input_args"]
        array_args = self.bench.info["array_args"]
        inputs = dict()
        for arg in input_args:
            if arg not in array_args:
                inputs.update(
                    {arg: self.bench.get_data(preset=self.preset)[arg]}
                )
            else:
                inputs.update({arg: self.copied_args[arg]})

        # Warmup
        @tout.exit_after(self.timeout)
        def warmup(impl_fn, inputs):
            impl_fn(**inputs)

        with timer.timer() as t:
            try:
                warmup(self.impl_fn, inputs)
            except Exception as e:
                warnings.warn("Benchmark execution failed")
                print(e)
                self.results.error_state = -3
                self.results.error_msg = "Execution failed"
                return

        self.results.warmup_time = t.get_elapsed_time()
        self._reset_output_args(inputs=inputs)
        exec_times = np.empty(self.repeat, dtype=np.float64)

        retval = None
        for i in range(self.repeat):
            with timer.timer() as t:
                retval = self.impl_fn(**inputs)
            exec_times[i] = t.get_elapsed_time()
            # Do not reset the output from the last repeat
            if i < self.repeat - 1:
                self._reset_output_args(inputs=inputs)

        self.results.exec_times = exec_times

        # Get the output data
        try:
            out_args = self.bench.info["output_args"]
        except KeyError:
            out_args = []

        array_args = self.bench.info["array_args"]
        with timer.timer() as t:
            for out_arg in out_args:
                if out_arg in array_args:
                    self.results.results.update(
                        {out_arg: self.fmwrk.copy_from_func()(inputs[out_arg])}
                    )
        self.results.teardown_time = t.get_elapsed_time()

        # Special case: if the benchmark implementation returns anything, then
        # add that to the results dict

        if retval:
            self.results.results.update({"return-value": retval})

    def get_results(self):
        return self.results


class Benchmark(object):
    """A class for reading and benchmark information and initializing
    benchmark data.
    """

    def _check_if_valid_impl_postfix(self, impl_postfix: str) -> bool:
        """Checks if an implementation postfix is found in the
        impl_postfix.json.

        Args:
            impl_postfix (str): An implementation postfix

        Returns:
            bool: True if the postfix is found in the JSON file else False
        """
        impl_postfixes = get_supported_implementation_postfixes()
        if impl_postfix in impl_postfixes:
            return True
        else:
            return False

    def _set_implementation_fn_list(self, bmod, initialize_fname):
        """Selects all the callables from the __all__ list for the module
        excluding the initialize function that we know is not a benchmark
        implementation.

        Args:
            bmod : A benchmark module
            initialize_fname : Name of the initialization function
        """

        return [
            fn
            for fn in getmembers(bmod, callable)
            if initialize_fname not in fn[0]
        ]

    def _load_benchmark_info(self, bconfig_path: str = None):
        """Reads the benchmark configuration and loads into a member dict.

        Args:
            bconfig_path (str, optional): _description_. Defaults to None.
        """
        bench_filename = "{b}.json".format(b=self.bname)
        bench_path = None

        if bconfig_path:
            bench_path = bconfig_path.joinpath(bench_filename)
        else:
            parent_folder = pathlib.Path(__file__).parent.absolute()
            bench_path = parent_folder.joinpath(
                "..", "configs", "bench_info", bench_filename
            )

        try:
            with open(bench_path) as json_file:
                self.info = json.load(json_file)["benchmark"]
        except Exception:
            warnings.warn(
                "Benchmark JSON file {b} could not be opened.".format(
                    b=bench_filename
                )
            )
            raise

    def _set_data_initialization_fn(self, bmodule):
        """Sets the initialize function object to be used by the benchmark.

        Raises:
            RuntimeError: If the module's initialize function could not be
            loaded.
        """

        if "init" in self.info.keys() and self.info["init"]:
            self.init_fn_name = self.info["init"]["func_name"]
            self.initialize_fn = getattr(bmodule, self.init_fn_name)
        else:
            raise RuntimeError(
                "Initialization function not specified in JSON configuration"
                + " for "
                + self.bname
            )

    def _set_reference_implementation(self, impl_fnlist):
        """Sets the reference implementation for the benchmark.

        The reference implementation is either a pure Python implementation
        if available, or else a NumPy implementation. If neither is found, then
        the reference implementation is set to None.

        Args:
            impl_fnlist : The list of implementation function for the
            benchmark.
        """
        ref_impl_fn = None

        for fn in impl_fnlist:
            if "python" in fn[0]:
                ref_impl_fn = fn
            elif "numpy" in fn[0]:
                ref_impl_fn = fn

        return ref_impl_fn

    def _set_impl_to_framework_map(self, impl_fnlist):
        """Create a dictionary mapping each implementation function name to a
        corresponding Framework object.

        Args:
            impl_fnlist : list of implementation functions

        Returns:
            Dict: Dictionary mapping implementation function to a Framework
        """

        impl_to_fw_map = dict()

        for bimpl in impl_fnlist:

            if "_numba" in bimpl[0] and "_dpex" not in bimpl[0]:
                impl_to_fw_map.update({bimpl[0]: dpbi.NumbaFramework("numba")})
            elif "_numpy" in bimpl[0]:
                impl_to_fw_map.update({bimpl[0]: dpbi.Framework("numpy")})
            elif "_python" in bimpl[0]:
                impl_to_fw_map.update({bimpl[0]: dpbi.Framework("python")})
            elif "_dpex" in bimpl[0]:
                try:
                    fw = dpbi.NumbaDpexFramework("numba_dpex")
                    impl_to_fw_map.update({bimpl[0]: fw})
                except Exception as e:
                    warnings.warn(
                        "Framework could not be created for numba_dpex due to:"
                        + e.__str__
                    )
            elif "_sycl" in bimpl[0]:
                try:
                    fw = dpbi.DpcppFramework("dpcpp")
                    impl_to_fw_map.update({bimpl[0]: fw})
                except Exception as e:
                    warnings.warn(
                        "Framework could not be created for dpcpp due to:"
                        + e.__str__
                    )
            elif "_dpnp" in bimpl[0]:
                # FIXME: Fix the dpnp framework and implementations
                warnings.warn(
                    "DPNP Framework is broken, skipping dpnp implementation"
                )

        return impl_to_fw_map

    def _get_validation_data(self, preset):
        if preset in self.refdata.keys():
            return self.refdata[preset]

        ref_impl_postfix = self.ref_impl_fn[0][
            (len(self.bname) - len(self.ref_impl_fn[0]) + 1) :  # noqa: E203
        ]

        ref_results = self.run(
            implementation_postfix=ref_impl_postfix,
            preset=preset,
            repeat=1,
            validate=False,
        )[0]

        if ref_results.error_state == 0:
            self.refdata.update({preset: ref_results.results})
            return ref_results.results
        else:
            warnings.warn(
                "Validation data unavailable as reference implementation "
                + "could not be executed."
            )
            return None

    def _validate_results(self, preset, frmwrk, frmwrk_out):

        ref_out = self._get_validation_data(preset)
        if not ref_out:
            return False
        try:
            validator_fn = frmwrk.validator()
            for key in ref_out.keys():
                valid = validator_fn(ref_out[key], frmwrk_out[key])
            return valid
        except Exception:
            return False

    def __init__(self, bmodule: object, bconfig_path: str = None):
        """Reads benchmark information.
        :param bname: The benchmark name.
        "param config_path: Optional location of the config JSON file for the
        benchmark. If none is provided, the default config inside the
        package's bench_info directory is used.
        """
        self.bname = bmodule.__name__.split(".")[-1]
        self.bdata = dict()
        self.refdata = dict()
        try:
            self._load_benchmark_info(bconfig_path)
            self._set_data_initialization_fn(bmodule)
            self.impl_fnlist = self._set_implementation_fn_list(
                bmodule, self.init_fn_name
            )
            self.ref_impl_fn = self._set_reference_implementation(
                self.impl_fnlist
            )
            self.impl_to_fw_map = self._set_impl_to_framework_map(
                self.impl_fnlist
            )
        except Exception:
            raise

    def get_impl_fnlist(self):
        """Returns a list of function objects each for a single implementation
        of the benchmark.

        Returns:
            list[tuple(str, object)]: A list of 2-tuple. The first element of
            the tuple is the string function name and the second element is
            the actual function object.
        """
        return self.impl_fnlist

    def has_impl(self, impl_postfix: str):

        if not impl_postfix:
            return False

        impls = [
            impl
            for impl in self.impl_fnlist
            if self.bname + "_" + impl_postfix == impl[0]
        ]
        if len(impls) == 1:
            return True
        else:
            return False

    def get_impl(self, impl_postfix: str):

        if not impl_postfix:
            return None

        fn = [
            impl[1]
            for impl in self.impl_fnlist
            if self.bname + "_" + impl_postfix == impl[0]
        ]
        if len(fn) > 1:
            warnings.warn(
                "Unable to select any implementation as there are "
                + "multiple implementations for "
                + impl_postfix
            )
            return None
        elif not fn:
            warnings.warn(
                "No implementation exists for postfix: " + impl_postfix
            )
            return None
        else:
            return fn[0]

    def get_framework(self, impl_postfix: str) -> Framework:
        try:
            return self.impl_to_fw_map[self.bname + "_" + impl_postfix]
        except KeyError:
            warnings.warn(
                "No framework found for the implementation "
                + self.bname
                + "_"
                + impl_postfix
            )
            return None

    def get_data(self, preset: str = "L") -> Dict[str, Any]:
        """Initializes the benchmark data.
        :param preset: The data-size preset (S, M, L, paper).
        """

        if preset in self.bdata.keys():
            return self.bdata[preset]

        # 1. Create data dictionary
        data = dict()

        # 2. Check if the provided preset configuration is available in the
        #    config file.
        if preset not in self.info["parameters"].keys():
            raise NotImplementedError(
                "{b} doesn't have a {p} preset.".format(b=self.bname, p=preset)
            )

        # 3. Store the input preset args in the "data" dict.
        parameters = self.info["parameters"][preset]
        for k, v in parameters.items():
            data[k] = v

        # 4. Call the initialize_fn with the input args and store the results
        #    in the "data" dict.

        init_input_args_list = self.info["init"]["input_args"]
        init_input_args_val_list = []
        for arg in init_input_args_list:
            init_input_args_val_list.append(data[arg])

        init_kws = dict(zip(init_input_args_list, init_input_args_val_list))
        initialized_output = self.initialize_fn(**init_kws)

        # 5. Store the initialized output in the "data" dict. Note that the
        #    implementation depends on Python dicts being ordered. Thus, the
        #    code will not work with Python older than 3.7.
        for idx, out in enumerate(self.info["init"]["output_args"]):
            data.update({out: initialized_output[idx]})

        # 6. Update the benchmark data (self.bdata) with the generated data
        #    for the provided preset.
        self.bdata[preset] = data
        return self.bdata[preset]

    def run(
        self,
        implementation_postfix: str = None,
        preset: str = "S",
        repeat: int = 10,
        validate: bool = True,
        timeout: float = 200.0,
    ):
        results = []
        if implementation_postfix:
            # Run the benchmark for a specific implementation
            runner = BenchmarkRunner(
                bench=self,
                impl_postfix=implementation_postfix,
                preset=preset,
                repeat=repeat,
                timeout=timeout,
            )
            result = runner.get_results()
            if validate and result.error_state == 0:
                if self._validate_results(
                    preset, result.framework, result.results
                ):
                    result.validation_state = 0
                else:
                    result.validation_state = -1
                    result.error_state = -3
                    result.error_msg = "Validation failed"

            results.append(result)

        else:
            # Run the benchmark for all available implementations
            for impl in self.get_impl_fnlist():
                impl_postfix = impl[0][
                    (len(self.bname) - len(impl[0]) + 1) :  # noqa: E203
                ]
                runner = BenchmarkRunner(
                    bench=self,
                    impl_postfix=impl_postfix,
                    preset=preset,
                    repeat=repeat,
                    timeout=timeout,
                )
                result = runner.get_results()
                if validate and result.error_state == 0:
                    if self._validate_results(
                        preset, result.framework, result.results
                    ):
                        result.validation_state = 0
                    else:
                        result.validation_state = -1
                        result.error_state = -3
                        result.error_msg = "Validation failed"

                results.append(result)
        return results
