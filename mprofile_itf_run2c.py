import subprocess
import threading
import copy, os
import time
import json
from UTILS.colorful import *

# ubuntu command to kill process: kill -9 $(ps -ef | grep fuqingxu |grep python | grep -v grep | awk '{print $ 2}')

arg_base = ['python', 'main.py']
log_dir = '%s/'%time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())
run_group = "bench"
# base_conf = 'train.json'

n_run = 9
conf_override = {
    "config.py->GlobalConfig-->note":       
                [
                    "HistoryRolling(10itf) rx3 db",
                    "HistoryRolling(20itf) rx3 db",
                    "HistoryRolling(30itf) rx3 db",

                    "HistoryRolling(40itf) rx3 db",
                    "HistoryRolling(50itf) rx3 db",
                    "HistoryRolling(60itf) rx3 db",

                    "HistoryRolling(70itf) rx3 db",
                    "HistoryRolling(80itf) rx3 db",
                    "HistoryRolling(90itf) rx3 db",
                ],

    "MISSIONS.collective_assult.collective_assult_parallel_run.py->ScenarioConfig-->random_jam_prob":       
                [
                    0.10,
                    0.20,
                    0.30,

                    0.40,
                    0.50,
                    0.60,

                    0.70,
                    0.80,
                    0.90,
                ],

    "config.py->GlobalConfig-->seed":       
                [
                    88,
                    88,
                    88,

                    88,
                    88,
                    88,

                    88,
                    88,
                    88,
                ],
    "config.py->GlobalConfig-->device":       
                [
                    "cuda:0",
                    "cuda:1",
                    "cuda:2",

                    "cuda:3",
                    "cuda:4",
                    "cuda:0",

                    "cuda:1",
                    "cuda:2",
                    "cuda:3",
                ],
    "config.py->GlobalConfig-->gpu_party":       
                [
                    "Cuda0-Party0",
                    "Cuda1-Party0",
                    "Cuda2-Party0",

                    "Cuda3-Party0",
                    "Cuda4-Party0",
                    "Cuda0-Party0",

                    "Cuda1-Party0",
                    "Cuda2-Party0",
                    "Cuda3-Party0",
                ],

}

base_conf = {
    # // python main.py -c d12-conc-orig.jsonc
    "config.py->GlobalConfig": {
        "note": "train_rolling(his_dualing)(80 itf)",
        "env_name":"collective_assult",
        "env_path":"MISSIONS.collective_assult",
        "draw_mode": "Img",
        "num_threads": "64",
        "report_reward_interval": "64",
        "test_interval": "2048",
        "device": "cuda:2",
        "gpu_party": "Cuda2-Party0",
        "fold": "1",
        "seed": 9996,
        "upload_after_test": "True",
        "backup_files":[
            "ALGORITHM/concentration_addhist_push2x/net.py",
            "ALGORITHM/concentration_addhist_push2x/ppo.py",
            "ALGORITHM/concentration_addhist_push2x/shell_env.py",
            "ALGORITHM/concentration_addhist_push2x/foundation.py",
            "ALGORITHM/concentration_addhist_push2x/trajectory.py",
            "ALGORITHM/concentration_addhist_push2x/cython_func.pyx",
            "MISSIONS/collective_assult/envs/collective_assult_env.py"
        ]
    },

    "MISSIONS.collective_assult.collective_assult_parallel_run.py->ScenarioConfig": {
        "size": "5",
        "random_jam_prob": 0.80,
        "introduce_terrain":"True",
        "terrain_parameters": [0.05, 0.2],
        "num_steps": "180",
        "render":"False",
        "render_with_unity":"False",
        "MCOM_DEBUG":"False",
        "render_ip_with_unity": "cn-cd-dx-1.natfrp.cloud:55861",
        "half_death_reward": "True",
        "TEAM_NAMES": [
            "ALGORITHM.concentration_addhist_push2x.foundation->ReinforceAlgorithmFoundation"
        ]
    },

    "ALGORITHM.concentration_addhist_push2x.foundation.py->AlgorithmConfig": {
        "n_focus_on": 2,
        "actor_attn_mod": "False",
        "extral_train_loop": "False",
        "lr": 5e-4,
        "ppo_epoch": 24,
        "train_traj_needed": "64",
        "load_checkpoint": False
    }
}





assert '_' not in run_group, ('下划线在matlab中的显示效果不好')
exp_log_dir = log_dir+'exp_log'
if not os.path.exists('PROFILE/%s'%exp_log_dir):
    os.makedirs('PROFILE/%s'%exp_log_dir)
exp_json_dir = log_dir+'exp_json'
if not os.path.exists('PROFILE/%s'%exp_json_dir):
    os.makedirs('PROFILE/%s'%exp_json_dir)


new_json_paths = []
for i in range(n_run):
    conf = copy.deepcopy(base_conf)
    new_json_path = 'PROFILE/%s/run-%d.json'%(exp_json_dir, i+1)
    for key in conf_override:
        assert n_run == len(conf_override[key]), ('检查！n_run是否对应')
        tree_path, item = key.split('-->')
        conf[tree_path][item] = conf_override[key][i]
    with open(new_json_path,'w') as f:
        json.dump(conf, f, indent=4)
    print(conf)
    new_json_paths.append(new_json_path)











final_arg_list = []
printX = [print红,print绿,print黄,print蓝,print紫,print靛,print亮红,print亮绿,print亮黄,print亮蓝,print亮紫,print亮靛]

for ith_run in range(n_run):
    final_arg = copy.deepcopy(arg_base)
    final_arg.append('--cfg')
    final_arg.append(new_json_paths[ith_run])
    final_arg_list.append(final_arg)
    print('')

def worker(ith_run):
    log_path = open('PROFILE/%s/run-%d.log'%(exp_log_dir, ith_run+1), 'w+')
    printX[ith_run%len(printX)](final_arg_list[ith_run])
    res = subprocess.run(final_arg_list[ith_run], stdout=log_path, stderr=log_path)
    print('worker end')

def clean_process(pid):
    import psutil
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        try:
            print亮红('sending Terminate signal to', child)
            child.terminate()
            time.sleep(5)
            print亮红('sending Kill signal to', child)
            child.kill()
        except: pass
    parent.kill()

def clean_up():
    print亮红('clean up!')
    parent_pid = os.getpid()   # my example
    clean_process(parent_pid)


if __name__ == '__main__':
        
    input('确认执行？')
    input('确认执行！')

    t = 0
    while (t >= 0):
        print('运行倒计时：', t)
        time.sleep(1)
        t -= 1

    threads = [ threading.Thread( target=worker,args=(ith_run,) ) for ith_run in range(n_run) ]
    for thread in threads:
        thread.setDaemon(True)
        thread.start()
        print('错峰执行，启动', thread)
        DELAY = 3
        for i in range(DELAY):
            print('\r 错峰执行，启动倒计时%d     '%(DELAY-i), end='', flush=True)
            time.sleep(1)

    from atexit import register
    register(clean_up)
    while True:
        is_alive = [thread.is_alive() for thread in threads]
        if any(is_alive):
            time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
            print(time_now, 'I am still running!', is_alive)
            print靛('current scipt:%s, current log:%s'%(os.path.abspath(__file__), 'PROFILE/%s/run-%d.log'%(exp_log_dir, ith_run+1)))
            time.sleep(60)
        else:
            break
    print('[profile] All task done!')
    for thread in threads:
        thread.join()