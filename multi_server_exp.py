
# ubuntu command to kill process: kill -9 $(ps -ef | grep xrdp | grep -v grep | awk '{print $ 2}')

n_run = 1
n_run_mode = [
    {
        "addr": "172.18.116.149:2233",
        "usr": "hmp",
        "pwd": "hmp"
    },
]
 

conf_override = {
    "config.py->GlobalConfig-->note":       
                [
                    "train_origin_T(5itf) t5",
                ],

    "MISSIONS.collective_assult.collective_assult_parallel_run.py->ScenarioConfig-->random_jam_prob":       
                [
                    0.05,
                ],

    "config.py->GlobalConfig-->seed":       
                [
                    22222221,
                ],
    "config.py->GlobalConfig-->device":       
                [
                    "cuda:0",
                ],
    "config.py->GlobalConfig-->gpu_party":       
                [
                    "off",
                ],

}



base_conf = {
    "config.py->GlobalConfig": {
        # please checkout config.py for information 15.9GB 22.1(11.4+435) 28.7 42GB
        "note": "example experiment7",                  # Very Important! in case you forget the purpose of this trainning session, write a note
        "env_name": "collective_assult",                # which environment, see ./MISSIONS/env_router.py
        "env_path": "MISSIONS.collective_assult",       # path of environment
        "draw_mode": "OFF",                             # activate data plotting (Tensorboard is not used because I do not like it)
        "num_threads": "64",                            # run N parallel envs, a 'env' is refered to as a 'thread'
        "report_reward_interval": "64",                 # reporting interval
        "test_interval": "2048",                        # test every $test_interval episode
        "fold": "1",                                    # this 'folding' is designed for IPC efficiency, you can thank python GIL for such a strange design... 
        "seed": 2222,                                   # seed controls pytorch and numpy
        "backup_files": [                               # backup files, pack them up
            "example.jsonc",
            "ALGORITHM/conc",
            "MISSIONS/collective_assult/envs/collective_assult_env.py"
        ],
        "device": "cuda:4",                             # choose from 'cpu' (no GPU), 'cuda' (auto select GPU), 'cuda:3' (manual select GPU) 
        # GPU memory is precious! assign multiple training process to a 'party', then they will share GPU memory 
        "gpu_party": "off",                     # default is 'off', 
        "upload_after_test": "True"
    },

    "UTILS.exp_upload.py->DataCentralServer": {
        "addr": "172.18.112.16", 
        "usr": "fuqingxu", 
        "pwd": "clara"
    },

    "MISSIONS.collective_assult.collective_assult_parallel_run.py->ScenarioConfig": {
        # please checkout ./MISSIONS/collective_assult/collective_assult_parallel_run.py for information
        "size": "5",
        "random_jam_prob": 0.05,
        "introduce_terrain": "True",
        "terrain_parameters": [
            0.05,
            0.2
        ],
        "num_steps": "180",
        "render": "False",
        "render_with_unity": "False",
        "MCOM_DEBUG": "False",
        "render_ip_with_unity": "cn-cd-dx-1.natfrp.cloud:55861",
        "half_death_reward": "True",
        "TEAM_NAMES": [
            "ALGORITHM.conc.foundation->ReinforceAlgorithmFoundation"
        ]
    },
    "ALGORITHM.conc.foundation.py->AlgorithmConfig": {
        # please checkout ./ALGORITHM/conc/foundation.py for information
        "n_focus_on": 2,
        "actor_attn_mod": "False",
        "extral_train_loop": "False",
        "lr": 0.0005,
        "ppo_epoch": 24,
        "train_traj_needed": "64",
        "load_checkpoint": "False"
    }
}

##############################################################################
##############################################################################
##############################################################################

import subprocess
import threading
import copy, os
import time
import json
from UTILS.colorful import *
arg_base = ['python', 'main.py']
time_mark = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())
log_dir = '%s/'%time_mark
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


def local_worker(ith_run):
    log_path = open('PROFILE/%s/run-%d.log'%(exp_log_dir, ith_run+1), 'w+')
    printX[ith_run%len(printX)](final_arg_list[ith_run])
    subprocess.run(final_arg_list[ith_run], stdout=log_path, stderr=log_path)

def remote_worker(ith_run):
    # step 1: transfer all files
    from UTILS.exp_upload import get_ssh_sftp
    addr = n_run_mode[ith_run]['addr']
    usr = n_run_mode[ith_run]['usr']
    pwd = n_run_mode[ith_run]['pwd']
    ssh, sftp = get_ssh_sftp(addr, usr, pwd)
    sftp.mkdir('/home/%s/MultiServerMission'%(usr), ignore_existing=True)
    sftp.mkdir('/home/%s/MultiServerMission/%s'%(usr, time_mark), ignore_existing=True)
    src_path = '/home/%s/MultiServerMission/%s/src'%(usr, time_mark)

    sftp.mkdir(src_path, ignore_existing=True)
    sftp.put_dir('./', src_path, ignore_list=['.vscode', '__pycache__','RECYCLE','ZHECKPOINT'])
    sftp.close()
    print亮紫('upload complete')


    # step 2: open byobu, execute trainning
    byobu_win_name = '%s--run-%d'%(time_mark, ith_run)
    byobu_win_name = byobu_win_name.replace(':','-')
    stdin, stdout, stderr = ssh.exec_command(command='byobu new-session -d -s %s'%byobu_win_name, timeout=1)
    # cd into it
    cmd = 'cd  ' + src_path
    stdin, stdout, stderr = ssh.exec_command(command='byobu send-keys "%s" C-m'%cmd, timeout=1)

    cmd = 'cd  ' + src_path
    stdin, stdout, stderr = ssh.exec_command(command='byobu send-keys "%s" C-m'%cmd, timeout=1)

    cmd = ' '.join(final_arg_list[ith_run])
    stdin, stdout, stderr = ssh.exec_command(command='byobu send-keys "%s" C-m'%cmd, timeout=1)
    print('远程代码运行成功')

    # 杀死
    stdin, stdout, stderr = ssh.exec_command(command='byobu kill-session -t %s'%byobu_win_name, timeout=1)
    pass

def worker(ith_run):
    if n_run_mode[ith_run] is None: 
        local_worker(ith_run)
    else:
        remote_worker(ith_run)



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
        
    # input('确认执行？')
    # input('确认执行！')

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
