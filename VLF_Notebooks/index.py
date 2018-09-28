import sys
import subprocess
import numpy as np
import pandas as pd
##pip3 install pyslha
#import pyslha # not longer required
import tempfile
import os
import re
import nose
#General config: TODO, make config file and use standard module
MADGRAPH='madgraph' # configure MadGraph dir here!
NO_TEST=False

def grep(pattern,multilinestring):
    '''Grep replacement in python
    as in: $ echo $multilinestring | grep pattern
    dev: re.M is for multiline strings
    '''
    import re 
    grp=re.finditer('(.*)%s(.*)' %pattern, multilinestring,re.M)
    return '\n'.join([g.group(0) for g in grp])

def subprocess_line_by_line(*args,TRUST_ERRORS=True,**kwargs):
    '''
    Subprocess output line by line. Stop of error found when TRUST_ERRORS=True, and simply
    report wait method otherwise.
    
    The arguments are the same as for the Popen constructor.
    
    WARNING: Works only in Python 3
    
    See: https://stackoverflow.com/a/28319191/2268280 
    and: https://stackoverflow.com/a/17698359/2268280
    
    Example:
    
    subprocess_line_by_line('for i in $(seq 1 3);do echo $i; sleep 1;done',shell=True)
    '''
    
    if not TRUST_ERRORS:
        kwargs['stderr']=subprocess.PIPE
        
    kwargs['stdout']=subprocess.PIPE
    kwargs['bufsize']=1
    kwargs['universal_newlines']=True
    s=subprocess.Popen(*args,**kwargs)
    with s as p:
        for line in p.stdout:
            print(line, end='') # process line here
    
    if TRUST_ERRORS:
        if p.returncode != 0:
            raise subprocess.CalledProcessError(p.returncode, p.args)
    else:
        return s.wait()
    
##Main madGRAPH script:
def preamble(cfg):
    return '''import model '''+cfg.UFO_model+'''
define p = g u c d s b u~ c~ d~ s~ b~
define j = p  
define l+ = e+ mu+ 
define l- = e- mu- 
define vl = ve vm vt 
define vl~ = ve~ vm~ vt~

'''+cfg.processes+'''

output ../'''+cfg.work_dir+'''/'''+cfg.output_dir+'''

'''

def lamL_loop(MH0,MHc,MA0,lamL,cfg):
    mg5_script='launch ../{:s}/{:s}\n'.format(cfg.work_dir,cfg.output_dir)
    mg5_script=mg5_script+'0\n'
    mg5_script=mg5_script+'{:s}\n'.format(cfg.LHA_input_file)
    mg5_script=mg5_script+'{:s}\n'.format(cfg.Card_file)
    mg5_script=mg5_script+'set nevents {:d}\n'.format(cfg.number_of_events)
    if MH0>0:
        mg5_script=mg5_script+'set wa0 auto\n'
        mg5_script=mg5_script+'set whch auto \n'
        mg5_script=mg5_script+'set lamL {:s}\n'.format(str(lamL))
        mg5_script=mg5_script+'set mmh0 {:s}\n'.format(str(MH0))
        mg5_script=mg5_script+'set mma0 {:s}\n'.format(str(MA0))
        mg5_script=mg5_script+'set mmhch {:s}\n'.format(str(MHc))
    mg5_script=mg5_script+'\n'
    mg5_script=mg5_script+'0\n'
    
    return mg5_script

def closing(cfg):
    return '''launch ../'''+cfg.work_dir+'''/'''+cfg.output_dir+''' -i
print_results --path=./result_'''+cfg.output_dir+'''.txt --format=short


done
'''

def check_root_install(cfg):
    cfg=pd.Series(cfg)
    f=open('kk.sh','w')
    f.write('source '+cfg.thisroot+'\n')
    f.write('which root\n')
    f.close()
    
    if not subprocess.Popen('bash kk.sh'.split(),
                stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[0]:
        sys.exit('INSTALL ROOT: see instrucctions in notebook')
        
def clone_git_repo(cfg,REPO='VBF_IDM',REPO_url='git@github.com:restrepo',git_options='--recursive'):
    cfg=pd.Series(cfg)
    if cfg.CLONE_GIT_REPO:  
        REPO
        REPO_url
         #WARNING: Try to overwirte contents
        if os.path.exists(cfg.main_dir+'index.ipynb'):
            sys.exit('ERROR: Repo files already exists. Check cfg.main_dir')
        if not os.path.isdir(cfg.main_dir):
            s=subprocess.Popen(['mkdir','-p',cfg.main_dir],stdout=subprocess.PIPE,stderr=subprocess.PIPE).wait()

        td=tempfile.mkdtemp()
        s=subprocess_line_by_line(('git clone  '+git_options+' '+REPO_url+'/'+REPO+'.git').split(),cwd=td,
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,TRUST_ERRORS=False)

        s=subprocess.Popen('mv '+td+'/'+REPO+'/*  '+cfg.main_dir,shell=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()

        s=subprocess.Popen('mv '+td+'/'+REPO+'/.* '+cfg.main_dir,shell=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()

        os.rmdir(td+'/'+REPO)
        os.rmdir(td)
    else:
        if cfg.VERBOSE:
            print('Skiping git clone')        
            
def install_pythia_delphes(cfg,release='v2.3.3'):
    if cfg.INSTALL:
        s=subprocess.Popen('git branch'.split(),cwd=cfg.MADGRAPH,
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()

        if not grep('\* '+release,s[0].decode('utf-8')):
            s=subprocess.Popen( ('git checkout -b '+release).split(),cwd=cfg.MADGRAPH,
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            if 'Switched' not in s[1].decode('utf-8'):
                sys.exit('Submodule problems')

        #subprocess does not use .bashrc        
        f=open(cfg.MADGRAPH+'/kk.sh','w')
        f.write('source '+cfg.thisroot+'\n')
        f.write('./bin/mg5_aMC install.dat\n')
        f.close()        
        if cfg.VERBOSE:
            subprocess_line_by_line('bash kk.sh'.split(),cwd=cfg.MADGRAPH, TRUST_ERRORS=False )
        else:
            s=subprocess.call('bash kk.sh'.split(),cwd=cfg.MADGRAPH, stdout=open('kk','w'),stderr=open('kkk','w') )
    else:
        if cfg.VERBOSE:
            print('Pythia: OK')
            print('Delphes: OK')  
                        
def not_html_opening(cfg):
    f=open(cfg.MADGRAPH+'/input/mg5_configuration.txt','r')
    mgc=f.read()
    f.close()

    f=open(cfg.MADGRAPH+'/input/mg5_configuration.txt','w')
    f.write(mgc.replace('# automatic_html_opening = True','automatic_html_opening = False'))
    f.close()           
            

def run_madgraph(MH0,MHc,MA0,LambdasL,cfg):
    # Prepare MadGraph-tools scripts directory
    s=subprocess.Popen(['mkdir','-p',cfg.work_dir+'/'+cfg.scripts_dir],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    
    # Creates MadGraph script
    f=open(cfg.work_dir+'/'+cfg.scripts_dir+'/'+cfg.MadGraph_script,'w')
    f.write( preamble(cfg) )
    for lamL in LambdasL:
        f.write( lamL_loop(MH0,MHc,MA0,lamL,cfg) )
    f.write( closing(cfg) )
    f.close()

    # Prepare MadGraph launch command (requeries source thisroot.sh confifurations)
    f=open(cfg.MADGRAPH+'/kk.sh','w')
    f.write('source '+cfg.thisroot+'\n')
    f.write('./bin/mg5_aMC ../'+cfg.work_dir+'/'+cfg.scripts_dir+'/'+cfg.MadGraph_script+'\n')
    f.close()

    # launch command from MadGraph directory
    if not cfg.VERBOSE:
        s=subprocess.Popen( 'bash kk.sh'.split(), cwd=cfg.MADGRAPH,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        s.wait()

    if cfg.VERBOSE:
        subprocess_line_by_line( 'bash kk.sh'.split(), cwd=cfg.MADGRAPH,TRUST_ERRORS=False)
        
def run_madevent(MH0,MHc,MA0,LambdasL,cfg):
    if len(LambdasL)>99:
        sys.exit('ERROR: UPDATE FORMAT FOR > 99 runs')
    # Prepares Pythia-Delphes script        
    f=open(cfg.work_dir+'/'+cfg.scripts_dir+'/'+cfg.pythia_script,'w')
    for r in range(1,len(LambdasL)+1):
        f.write('pythia run_%02d\n' %r)
        f.write('3\n')
        f.write(cfg.Delphes_card_file+'\n')
        f.write('0\n')
    f.close()

    # Prepare Pythia-Delphes launch command (requeries source thisroot.sh confifurations)
    f=open(cfg.work_dir+'/'+cfg.output_dir+'/kk.sh','w')
    f.write('source '+cfg.thisroot+'\n')
    f.write('./bin/madevent ../'+cfg.scripts_dir+'/'+cfg.pythia_script+'\n')
    
    f.close()

    # launch command from MadGraph-output directory
    (PHOUT,PHERR)=subprocess.Popen('bash kk.sh'.split(), cwd=cfg.work_dir+'/'+cfg.output_dir,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    #print(PHOUT.decode('utf-8'))
    DEBUG=True
    if DEBUG:
        f=open('PHOUT.txt','w')
        f.write(PHOUT.decode('utf-8'))
        f.close()

    # Analyse output to get the cross-section of each run
    cs_pb=np.array( re.sub( '\s+\+\-\s+[0-9\+\-eE\.]+\s+pb','\n',  
              re.sub('\s+Cross-section\s+:\s+','' ,
              ''.join( grep('Cross-section',PHOUT.decode('utf-8')).split('\n') 
              ) )  ).strip().split('\n')  ).astype(float)

    # Store cross section in a pandas DataFrame
    if len(cs_pb)==len(LambdasL):
        df=pd.DataFrame({'xs_'+str(int(MH0)):cs_pb,'laL':LambdasL})
        return df
    else:
        sys.exit('Error: missing cross section')
        return pd.Series()
    
def store_output(MH0,MHc,MA0,LambdasL,cfg):
    s=subprocess.Popen(['mkdir', '-p',cfg.full_output_dir]).wait()

    for r in range(1,len(LambdasL)+1):
        nrun='%02d' %r
        nrun3='%03d' %r
        s=subprocess.Popen(['cp',cfg.work_dir+'/'+cfg.output_dir+'/Events/run_'+nrun+'/tag_1_delphes_events.root', 
                                cfg.full_output_dir+'/delphes_events_'+str(int(MH0))+'_'+nrun3+'_.root'],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if s.wait()>0:
            sys.exit('Files not found')

def merge_cross_sections_results(df,df_full=pd.read_csv('Output_data.csv')):
    dff=df_full.merge(df,on='laL',how='left').fillna(0)
    tmp=dff['laL']
    dff=dff.drop('laL',axis='columns')
    dff['laL']=tmp
    return dff

def main(scan_par,*input_par,only_config=False,skip_MadGraph=False,**cfg):
    '''
    Simulation of processes for each component of the scan_par list of the model through full chain 
    madgraph - Pythia -Delphes.
    
    Implemented model: Inert Doublet Model
    scan_par -> LambdaL list.
    input_par: List of the model parameters
        input_par[0] -> MH0
        input_par[1] -> MHc
        input_par[2] -> MA0
        
    Check main?? for **cfg options. 
    
    Default options are returned
    '''
    global MADGRAPH
    LambdasL=scan_par
    MH0=input_par[0]
    MHc=input_par[1]
    MA0=input_par[2]
    #Default values
    cfg=pd.Series(cfg)
    if 'thisroot' not in cfg:
        cfg['thisroot']='/home/restrepo/prog/ROOT/root/bin/thisroot.sh' 
        #cfg['thisroot']='/opt/root5/bin/thisroot.sh'
    if 'main_dir' not in cfg:
        cfg['main_dir']='.' # PATH of the .git of the cloned repository        
    if 'MADGRAPH' not in cfg:           
        cfg['MADGRAPH']=MADGRAPH # Name of the MadGraph installation. Configured at beggining        
    if 'Card_file' not in cfg:
        cfg['Card_file']='../Cards/run_card.dat'
    if 'number_of_events' not in cfg:
        cfg['number_of_events']=1000
    if 'UFO_model' not in cfg:
        cfg['UFO_model']='InertDoublet_UFO'
    if 'LHA_input_file' not in cfg:       
        cfg['LHA_input_file']='../MadGraph_cards/benchmarks/param_card_template.dat'
    #Loaded from cwd=cfg.work_dir+'/'+cfg.output_dir:
    if 'Delphes_card_file' not in cfg:       
        cfg['Delphes_card_file']='../../../Delphes_cards/delphes_card.dat'
    if 'processes' not in cfg:        
        cfg['processes']='generate p p > h2 h2 j j @0'        
        #cfg['processes']='generate p p > h2 h2'                
    if 'work_dir' not in cfg:        
        cfg['work_dir']='studies/IDM/' # Directory with the MadGraph-tools scripts        
    if 'scripts_dir' not in cfg:
        cfg['scripts_dir']='Task_Asana' # subdirectory of 'work_dir' with the MadGraph-tools scripts        
    if 'output_dir' not in cfg:        
        cfg['output_dir']='BP_'+str(int(MHc))+'_'+str(int(MH0))+'_vs_lambdaL' # MadGraph output subdirectory of work_dir
    if 'MadGraph_script' not in cfg:       
        cfg['MadGraph_script']='BP_'+str(int(MHc))+'_A_'+str(int(MH0))+'.txt' # MadGraph script
    if 'pythia_script' not in cfg:        
        cfg['pythia_script']='TemplateRunPythiaDelphes_all.dat' # Pythia-Delphes script
    if 'full_output_dir' not in cfg:
        cfg['full_output_dir'] ='output' # Final results dir for root and csv files
    if 'cross_sections_csv' not in cfg:
        cfg['cross_sections_csv']='cs_'+str(int(MHc))+'_'+str(int(MH0))+'.csv' # Final csv output
    if 'CLONE_GIT_REPO' not in cfg:        
        cfg['CLONE_GIT_REPO']=True #WARNING: Try to overwrite current contents!
    if 'INSTALL' not in cfg:          
        cfg['INSTALL']=False # If True check full installation
        if cfg.CLONE_GIT_REPO:
            cfg.INSTALL=True
    if 'VERBOSE' not in cfg:      
        cfg['VERBOSE']=True #Print shell commands output line by line 
        
    if only_config:
        return cfg
    print('========= Preparing run...====')
    if not skip_MadGraph:
        check_root_install(cfg)
        if not os.path.isdir('.git'): 
            clone_git_repo(cfg)
        if not os.path.isdir(MADGRAPH+'/pythia-pgs'): 
            install_pythia_delphes(cfg)
            
        not_html_opening(cfg)
    
        print('========= Runnig MadGraph (shown here if VERBOSE=True ====')
        run_madgraph(MH0,MHc,MA0,LambdasL,cfg)
        
    print('========= Runnig MadEvent. This can take a long...====')
    df=run_madevent(MH0,MHc,MA0,LambdasL,cfg)
    
    print('========= Saving root and csv files in :===='+cfg.full_output_dir+'...')
                    
    store_output(MH0,MHc,MA0,LambdasL,cfg)
    
    df.to_csv(cfg.full_output_dir+'/'+cfg.cross_sections_csv,index=False)
    
    print('======== CONGRATULATIONS for the successful runs =====')

    return cfg

def test_repo():
    if os.path.isdir('.git'): 
        return True
    global NO_TEST
    NO_TEST=True
    MHc=750
    MH0=240
    MA0=MHc
    LambdasL=[0.01]

    cfg=main(LambdasL,MH0,MHc,MA0,MadGraph_script='test.txt',processes='generate p p > h2 h2',work_dir='test',
                 output_dir='tmp',full_output_dir='test',cross_sections_csv='test.csv',VERBOSE=False,
                 CLONE_GIT_REPO=True,INSTALL=True)
    df=pd.read_csv(cfg.full_output_dir+'/'+cfg.cross_sections_csv)
    nose.tools.assert_almost_equal(df.xs_240.values[0],5.288E-8)


def test_install():
    global MADGRAPH
    if os.path.isdir(MADGRAPH+'/pythia-pgs'): 
        return True
    global NO_TEST
    NO_TEST=True
    MHc=750
    MH0=240
    MA0=MHc
    LambdasL=[0.01]

    cfg=main(LambdasL,MH0,MHc,MA0,MadGraph_script='test.txt',processes='generate p p > h2 h2',work_dir='test',
                 output_dir='tmp',full_output_dir='test',cross_sections_csv='test.csv',VERBOSE=False,
                 CLONE_GIT_REPO=True,INSTALL=True)
    df=pd.read_csv(cfg.full_output_dir+'/'+cfg.cross_sections_csv)
    nose.tools.assert_almost_equal(df.xs_240.values[0],5.288E-8)
    
def test_all():
    '''run with: 
       $ nosetest3 thisprogram.py 
       .
       ----------------------------------------------------------------------
       Ran 1 test in 73.094s

       OK
       
    It is assumed that repo is already cloned and MadGraph tools have been installed
    '''
    if NO_TEST:
        return True
    MHc=750
    MH0=240
    MA0=MHc
    LambdasL=[0.01]

    cfg=main(LambdasL,MH0,MHc,MA0,MadGraph_script='test.txt',processes='generate p p > h2 h2',work_dir='test',
                output_dir='tmp',full_output_dir='test',cross_sections_csv='test.csv',VERBOSE=False,
            CLONE_GIT_REPO=False,INSTALL=False)
    df=pd.read_csv(cfg.full_output_dir+'/'+cfg.cross_sections_csv)
    nose.tools.assert_almost_equal(df.xs_240.values[0],5.288E-8)
    
if __name__=='__main__':
    VBF=True; MJ=False
    if not VBF:
        MJ=True
    BP={3:pd.Series({'MH0':65, 'MHc':200,'MA0':189.5,'LaL':0.009,'La2':0.1}),
        6:pd.Series({'MH0':65, 'MHc':500,'MA0':494,  'LaL':0.009,'La2':0.1}),
        7:pd.Series({'MH0':65, 'MHc':750,'MA0':750,  'LaL':0.009,'La2':0.1}),
        8:pd.Series({'MH0':65, 'MHc':750,'MA0':750,  'LaL':0.5,   'La2':0.1}),
        9:pd.Series({'MH0':110,'MHc':750,'MA0':750,  'LaL':0.009,'La2':0.1}),
        10:pd.Series({'MH0':0,'MHc':0,'MA0':0,  'LaL':0,'La2':0}),
        11:pd.Series({'MH0':100,'MHc':200,'MA0':105,  'LaL':1,'La2':1})
        }    
    N=11
    if MJ:
        N=9
    MH0=int(BP[N].MH0)
    MHc=int(BP[N].MHc)
    MA0=BP[N].MA0

    if MH0%1!=0 or MHc%1!=0:
        sys.exit('ERROR: MH0 and MHc must be integer')

    LambdasL=[BP[N].LaL]#,0.02,0.05,0.07,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.55,0.6,1.0,3.0,5.0,7.0,10.0]
    if MJ:
        LambdasL=[0.01,0.05,0.1,0.5,1.,2.]
    
    cfg=main(LambdasL,MH0,MHc,MA0,number_of_events=10000)    
