import argparse
import os
import sys
import copy
import shutil
import glob



def parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("INPUT", help="xyz file", nargs="*")
    parser.add_argument("-p", "--proc",  type=str, default=None, help='proc')
    parser.add_argument("-m", "--mem",  type=str, default=None, help='memory(words)')
    parser.add_argument("-func", "--functional",  type=str, default='wB97XD', help='functional for DFT (ex.) wB97XD(default), B3LYP')
    parser.add_argument("-b", "--basisset",  type=str, default='def2SVP', help='basis set (after typing basis set and space, you can spcify SCRF=(SMD,Solvent=water), Empricaldispersion=GD3, Int(Grid=Fine) etc.) (ex.) def2SVP(default), 6-31G(d), STO-3G, "def2SVP SCRF=(SMD,Solvent=water)", ')
    parser.add_argument("-c", "--charge",  type=str, default='0', help='charge')
    parser.add_argument("-s", "--spin",  type=str, default='1', help='bspin multiply')
    parser.add_argument('-t','--theory',  type=str, default='MIN', help='MIN SADDLE LUP etc.')
    parser.add_argument('-nf','--nofolder', help="dont make folder.", action='store_true')
    parser.add_argument('-sf','--samefolder', type=str,nargs="?",help="save same folder.")
    parser.add_argument("-all", "--allxyz", help="convert to .com file from all .xyz file in this directory.", action='store_true')
    parser.add_argument("-o","--options", help="options (ex.) -o NOFC MaxOPTITR=0 MinFreqValue=50 DontKeepGauCHK Gaumem=100 Gauproc=1 (default) Gaumem=1500 GauProc=16 MinFreqValue=50.0 EigenCheck DontKeepGauCHK DownDC=50", nargs="*", default=["Gaumem=1500", "GauProc=16", "MinFreqValue=50.0", "EigenCheck", "DontKeepGauCHK", "DownDC=50"])
    parser.add_argument("-ma", "--manual_AFIR", nargs="*",  type=str, default=None, help='manual-AFIR (ex.) [[Whole gamma(kJ/mol)] [Gamma(kJ/mol) (If you do not want to write anything, just type "None".)] [Fragm.1(ex. 1,2,3-5)] [Fragm.2] ...]')
    parser.add_argument("-kp", "--keep_pot", nargs="*",  type=str, default=None, help='keep potential 0.5*k*(r - r0)^2 (ex.) [[spring const.(a.u.)] [keep distance (ang.)] [atom1,atom2] ...] ')
    parser.add_argument("-ta", "--target")
    args = parser.parse_args()

    for i in range(len(args.options)):
        if args.proc is not None:
            if "Proc=" in args.options[i]:
                tmp_word = args.options[i].split("=")[0]+"="+str(args.proc)
                args.options[i] = copy.copy(tmp_word)

            elif "Proc =" in args.options[i]:
                tmp_word = args.options[i].split("=")[0]+"="+str(args.proc)
                args.options[i] = copy.copy(tmp_word)

            elif "proc=" in args.options[i]:
                tmp_word = args.options[i].split("=")[0]+"="+str(args.proc)
                args.options[i] = copy.copy(tmp_word)

            elif "proc =" in args.options[i]:
                tmp_word = args.options[i].split("=")[0]+"="+str(args.proc)
                args.options[i] = copy.copy(tmp_word)
            else:
                pass
        
        if args.mem is not None:
            if "mem=" in args.options[i]:
                tmp_word = args.options[i].split("=")[0]+"="+str(args.mem)
                args.options[i] = copy.copy(tmp_word)

            elif "Mem=" in args.options[i]:
                tmp_word = args.options[i].split("=")[0]+"="+str(args.mem)
                args.options[i] = copy.copy(tmp_word)

            elif "mem =" in args.options[i]:
                tmp_word = args.options[i].split("=")[0]+"="+str(args.mem)
                args.options[i] = copy.copy(tmp_word)

            elif "Mem =" in args.options[i]:
                tmp_word = args.options[i].split("=")[0]+"="+str(args.mem)
                args.options[i] = copy.copy(tmp_word)
            else:
                pass


    return args


class xyz2GRRMcom:
    def __init__(self, args):
        self.args = args


    def num_parse(self, numbers):
        sub_list = []
        
        sub_tmp_list = numbers.split(",")
        for sub in sub_tmp_list:                        
            if "-" in sub:
                for j in range(int(sub.split("-")[0]),int(sub.split("-")[1])+1):
                    sub_list.append(j)
            else:
                sub_list.append(int(sub))    
        return sub_list

    def force_data_parse(self):
        force_data = {}
        force_data["whole_gamma"] = None
        force_data["gamma_list"] = []
        force_data["fragm_A_list"] = []
        force_data["fragm_B_list"] = []
        if self.args.manual_AFIR is not None:
            force_data["whole_gamma"] = self.args.manual_AFIR[0]
            if len(self.args.manual_AFIR[1:]) % 3 != 0:
                print("invalid input (-ma)")
                sys.exit(1)

            for i in range(int(len(self.args.manual_AFIR[1:])/3)):
                force_data["gamma_list"].append(self.args.manual_AFIR[3*i+1])
                force_data["fragm_A_list"].append(self.args.manual_AFIR[3*i+2])
                force_data["fragm_B_list"].append(self.args.manual_AFIR[3*i+3])
        else:
            pass


        force_data["keeppot_spring_const"] = []
        force_data["keeppot_eq_dist"] = []
        force_data["keeppot_atom_pair"] = []

        if self.args.keep_pot is not None:
            if len(self.args.keep_pot) % 3 != 0:
                print("invalid input (-kp)")
                sys.exit(1)
            for i in range(int(len(self.args.keep_pot)/3)):
                force_data["keeppot_spring_const"].append(self.args.keep_pot[3*i+0])
                force_data["keeppot_eq_dist"].append(self.args.keep_pot[3*i+1])
                force_data["keeppot_atom_pair"].append(list(map(str, self.num_parse(self.args.keep_pot[3*i+2]))))
        else:
            force_data["keeppot_spring_const"] = None

        self.force_data = force_data
        


    def folder_maker(self, file):

        try:
            print(file)
            os.mkdir(str(file[:-4]+"_job"))
            shutil.move(file,"./"+str(file[:-4])+"_job"+"/"+os.path.basename(file))
        except Exception as e:
            print(e)

        return
        
    def same_folder_maker(self):
        file_list = glob.glob("./*.com")
        try:
            os.mkdir(str(self.args.samefolder+"_job"))
        except:
            pass
        
        for file in file_list:
            print(file)
            shutil.move(file,"./"+str(self.args.samefolder)+"_job"+"/"+os.path.basename(file))

        return

    def make_AFIR_input(self):
        AFIR_input_list = ["Add interaction"]
        AFIR_input_list.append("Gamma="+self.force_data["whole_gamma"])
        for i in range(len(self.force_data["gamma_list"])):
            AFIR_input_list.append("Fragm."+str(2*i+1)+"="+self.force_data["fragm_A_list"][i])
            AFIR_input_list.append("Fragm."+str(2*i+2)+"="+self.force_data["fragm_B_list"][i])
        for i in range(len(self.force_data["gamma_list"])):
            if self.force_data["gamma_list"][i] != "None":
                AFIR_input_list.append(str(2*i+1)+" "+str(2*i+2)+"  "+self.force_data["gamma_list"][i])
            else:
                AFIR_input_list.append(str(2*i+1)+" "+str(2*i+2)+"  ")
        AFIR_input_list.append("END")
        return AFIR_input_list
    
    def make_KeepPot_input(self):
        KeepPot_input_list = []
        for i in range(len(self.force_data["keeppot_spring_const"])):
            
            KeepPot_input_list.append("AddKeepPotential="+str(self.force_data["keeppot_atom_pair"][i][0])+","+str(self.force_data["keeppot_atom_pair"][i][1])+"="+str(self.force_data["keeppot_spring_const"][i])+"; "+str(self.force_data["keeppot_atom_pair"][i][0])+" "+str(self.force_data["keeppot_atom_pair"][i][1])+" "+str(self.force_data["keeppot_eq_dist"][i]))
        return KeepPot_input_list


    def com_file_maker(self, file):
        with open(file,"r") as f:
            words = f.read().splitlines()

            
        with open(str(os.path.basename(file)[:-4])+".com","w") as f2:
            f2.write("# "+self.args.theory+"/"+self.args.functional+"/"+self.args.basisset)
            f2.write("\n\n"+self.args.charge+" "+self.args.spin+"\n")
            for word in words[2:]:
                f2.write(word+"\n")
            f2.write("Options\n")
            for option in self.args.options:
                f2.write(option+"\n")
            if self.force_data["whole_gamma"] is None:
                pass
            else:
                AFIR_input_list = self.make_AFIR_input()
                for input in AFIR_input_list:
                    f2.write(input+"\n")

            if self.force_data["keeppot_spring_const"] is None:
                pass
            else:
                KeepPot_input_list = self.make_KeepPot_input()
                for input in KeepPot_input_list:
                    f2.write(input+"\n")

        return

        
    def main(self, file_list):
        print(file_list)
        self.force_data_parse()
        for file in file_list:
            print(file)
            self.com_file_maker(file)

        #---------------
        print(self.args.samefolder)
        if self.args.samefolder != None:
            self.same_folder_maker(self.args.samefolder)
        elif not self.args.nofolder:
            for file in file_list:
                self.folder_maker(file)   
        else:
            pass
        #---------------
        return



if __name__ == "__main__":
    args = parser()
    x2g = xyz2GRRMcom(args)
    job_name = args.INPUT
    if args.allxyz:
        file_list = glob.glob("./*.xyz")
    else:

        if "*" in str(job_name):
                
            file_list = []
            for job in job_name:
                print(job)
                tmp = glob(job)
                file_list.extend(tmp)
        else:
            file_list = job_name


    x2g.main(file_list)

    print("complete...")
