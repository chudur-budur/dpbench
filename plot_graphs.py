import util
import options
import os, sys

try:
    import pandas as pd
except:
    print("Pandas not available\n")

# def plot_numba_CPU(app_name, cmds):
#     util.chdir("CPU")

#     df = pd.read_csv('perf_output.csv',names=['input_size','throughput'], index_col='input_size')

#     # this is needed for setting the layout to show complete figure
#     #from matplotlib import rcParams
#     #rcParams.update({'figure.autolayout': True})
    
#     bar_chart = df.plot.bar(legend=False,rot=45,fontsize=10)
#     #bar_chart.set(xlabel='Input size', ylabel='Thoughput in input elements Processed per second')
#     bar_chart.set_ylabel('Thoughput in input elements processed per second',fontsize=10)
#     bar_chart.set_xlabel('Input size',fontsize=10)
#     fig = bar_chart.get_figure()
#     fig_filename = str(app_name) + "_numba_CPU_performance.pdf"
#     fig.savefig(fig_filename,bbox_inches="tight")

#     #print(df)
#     return df.loc[cmds['ref_input'],'throughput']
        
# def plot_numba_GPU(app_name, cmds):
#     util.chdir("GPU")

#     df = pd.read_csv('perf_output.csv',names=['input_size','throughput'], index_col='input_size')

#     # this is needed for setting the layout to show complete figure
#     #from matplotlib import rcParams
#     #rcParams.update({'figure.autolayout': True})
    
#     bar_chart = df.plot.bar(legend=False,rot=45,fontsize=10)
#     #bar_chart.set(xlabel='Input size', ylabel='Thoughput in input elements Processed per second')
#     bar_chart.set_ylabel('Thoughput in input elements processed per second',fontsize=10)
#     bar_chart.set_xlabel('Input size',fontsize=10)
#     fig = bar_chart.get_figure()
#     fig_filename = str(app_name) + "_numba_GPU_performance.pdf"
#     fig.savefig(fig_filename,bbox_inches="tight")

#     #print(df)
#     return df.loc[cmds['ref_input'],'throughput']    
    
# def plot_native(opts, all_plot_data):
#     util.chdir("native")

#     native_dir = os.getcwd();
    
#     for app, cmds in opts.wls.wl_list.items():
#         if cmds['execute'] is True:

#             plot_data_entry = {}
#             if app in all_plot_data:
#                 plot_data_entry = all_plot_data[app]                
                
#             util.chdir(app)
#             app_dir = os.getcwd();
#             if opts.platform == options.platform.cpu or opts.platform == options.platform.all:
#                 cpu_perf = get_runtime_data(app, cmds, "CPU")
#                 plot_data_entry['native_cpu'] = cpu_perf
#                 util.chdir(app_dir)
                
#             if opts.platform == options.platform.gpu or opts.platform == options.platform.all:
#                 gpu_perf = get_runtime_data(app, cmds, "GPU")
#                 plot_data_entry['native_gpu'] = gpu_perf
                
#             util.chdir(native_dir)
#             all_plot_data[app] = plot_data_entry    

def get_runtime_data(app_name, cmds, platform):
    util.chdir(platform)

    df = pd.read_csv('runtimes.csv',names=['input_size','runtime'], index_col='input_size')
    
    # bar_chart = df.plot.bar(legend=False,rot=45,fontsize=10)
    # bar_chart.set_ylabel('Thoughput in input elements processed per second',fontsize=10)
    # bar_chart.set_xlabel('Input size',fontsize=10)
    # fig = bar_chart.get_figure()
    # fig_filename = str(app_name) + "_native_CPU_performance.pdf"
    # fig.savefig(fig_filename,bbox_inches="tight")

    #print(df)
    return df.loc[cmds['ref_input'],'runtime']

def get_runtimes(opts, all_plot_data, impl):
    util.chdir(impl)

    numba_dir = os.getcwd();
    
    for app, cmds in opts.wls.wl_list.items():
        if cmds['execute'] is True:

            plot_data_entry = {}
            if app in all_plot_data:
                plot_data_entry = all_plot_data[app]                
                
            util.chdir(app)
            app_dir = os.getcwd();
            if opts.platform == options.platform.cpu or opts.platform == options.platform.all:
                cpu_perf = get_runtime_data(app, cmds, "CPU")
                plot_data_entry[impl + '_cpu'] = cpu_perf
                util.chdir(app_dir)
                
            if opts.platform == options.platform.gpu or opts.platform == options.platform.all:
                gpu_perf = get_runtime_data(app, cmds, "GPU")
                plot_data_entry[impl + '_gpu'] = gpu_perf
                
            util.chdir(numba_dir)
            all_plot_data[app] = plot_data_entry

def check_envvars_tools(opts):
    if opts.analysis is not options.analysis.all and opts.analysis is not options.analysis.perf:
        print("Plotting can be run only with option --analysis(-a) set to all or perf. Exiting")
        sys.exit()

    try:
        import pandas
    except:
        print ("Pandas not available. Plotting disabled\n")
        sys.exit()

def plot_efficiency_graph(all_plot_data):
    df = pd.DataFrame.from_dict(all_plot_data, orient='index')

    df['cpu_efficiency'] = (df['numba_cpu']/df['native_cpu'])*100.00
    df['gpu_efficiency'] = (df['numba_gpu']/df['native_gpu'])*100.00

    df.drop(columns=['native_cpu', 'native_gpu', 'numba_cpu', 'numba_gpu'], inplace=True)

    bar_chart = df.plot.bar(rot=45,fontsize=10)
    bar_chart.set_ylabel('Efficiency in percentage',fontsize=10)
    bar_chart.set_xlabel('Benchmark',fontsize=10)
    fig = bar_chart.get_figure()
    fig_filename = "Efficiency_graph.pdf"
    fig.savefig(fig_filename,bbox_inches="tight")

def plot_speedup_graph(all_plot_data):
    df = pd.DataFrame.from_dict(all_plot_data, orient='index')

    df['native_speedup'] = (df['native_cpu']/df['native_gpu'])*100.00
    df['numba_speedup'] = (df['numba_cpu']/df['numba_gpu'])*100.00

    df.drop(columns=['native_cpu', 'native_gpu', 'numba_cpu', 'numba_gpu'], inplace=True)

    bar_chart = df.plot.bar(rot=45,fontsize=10)
    bar_chart.set_ylabel('Speedup in percentage',fontsize=10)
    bar_chart.set_xlabel('Benchmark',fontsize=10)
    fig = bar_chart.get_figure()
    fig_filename = "Speedup_graph.pdf"
    fig.savefig(fig_filename,bbox_inches="tight")
    
def run(opts):
    check_envvars_tools(opts)
    
    ref_cwd = os.getcwd();
    
    all_plot_data = {}
    
    if opts.impl == options.implementation.native or opts.impl == options.implementation.all:
        get_runtimes(opts, all_plot_data, "native")
        util.chdir(ref_cwd)
        
    if  opts.impl == options.implementation.numba or opts.impl == options.implementation.all:
        get_runtimes(opts, all_plot_data, "numba")
        util.chdir(ref_cwd)

    plot_efficiency_graph(all_plot_data)
    plot_speedup_graph(all_plot_data)
