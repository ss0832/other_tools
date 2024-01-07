import os
from glob import glob
import argparse


def parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("INPUT", help="file name to securely delete.", nargs="*")
    parser.add_argument("-z", "--zerowrite", help="zero write", action='store_true')
    parser.add_argument("-r", "--randwrite", help="random write", action='store_true')
    parser.add_argument("-f", "--nsarec", help="NSA recommended write", action='store_true')
    parser.add_argument("-n", "--number",  type=str, default='3', help='times to write meaningless data for deletion')
    
    args = parser.parse_args()
    job_name = args.INPUT
    ZERO_WRITE_FLAG = args.zerowrite
    RAND_WRITE_FLAG = args.randwrite
    NSA_REC_WRITE_FLAG = args.nsarec
    write_num = int(args.number)
    
    if "*" in str(job_name):
        file_list = []
        for job in job_name:
            print(job)
            tmp = glob(job)
        file_list.extend(tmp)
    else:
        file_list = job_name
    
    return file_list, ZERO_WRITE_FLAG, RAND_WRITE_FLAG, NSA_REC_WRITE_FLAG, write_num

def random_write_secure_delete(path, passes):
    with open(path, "ba+") as delfile:
        length = delfile.tell()
    with open(path, "br+") as delfile:
        for i in range(passes):
            delfile.seek(0)
            delfile.write(os.urandom(length))
            print("Pass %s Complete" % str(i))
    
    os.remove(path)
    return

def zero_write_secure_delete(path, passes):
    with open(path, "ba+") as delfile:
        length = delfile.tell()
    with open(path, "br+") as delfile:
        for i in range(passes):
            delfile.seek(0)
            delfile.write(length*b'\x00')
            print("Pass %s Complete" % str(i))
    
    os.remove(path)
    return


def NSA_recommended_secure_delete(path, passes):
    with open(path, "ba+", buffering=0) as delfile:
        length = delfile.tell()
    
    with open(path, "br+", buffering=0) as delfile:
        print("Length of file:%s" % str(length))
        for i in range(passes):
            delfile.seek(0,0)
            delfile.write(os.urandom(length))
            print("Pass %s Complete" % str(i))
        print("All %s Passes Complete" % str(passes))
        delfile.seek(0)
        for x in range(length):
            delfile.write(b'\x00')
    
    print("Final Zero Pass Complete")
    os.remove(path) 
    return


if __name__ == "__main__":
    file_list, ZERO_WRITE_FLAG, RAND_WRITE_FLAG, NSA_REC_WRITE_FLAG, passes = parser()
    input("if you input enter, I delete files (This process isn't undone.)")
    
    for file_path in file_list:
        print(file_path)
        if NSA_REC_WRITE_FLAG and os.path.exists(file_path):
            print("NSA recommended file secure deletion method")
            NSA_recommended_secure_delete(file_path, passes)
            
        if RAND_WRITE_FLAG and os.path.exists(file_path):
            print("random write file secure deletion method")
            random_write_secure_delete(file_path, passes)

        if ZERO_WRITE_FLAG and os.path.exists(file_path):
            print("zero write file secure deletion method")
            zero_write_secure_delete(file_path, passe)

    print("Completed...")