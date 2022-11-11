import os, re, glob
from subprocess import Popen, PIPE
from random import randint, randrange

class downloadRepositoryClass():
    def __init__(self, user_name, auth_token, ssh, repo_directory, repo, branch, scanner_directory_path):
        self.downloadRepo = True
        self.downloadRepoComplete = False
        self.user_name = user_name.replace('@', '%40')
        self.ssh_url = re.findall(r'(https\:\/\/)(.*)', ssh)
        self.git_url = self.ssh_url[0][0] + self.user_name + ':' + auth_token + '@' + self.ssh_url[0][1]
        self.repo_directory = repo_directory
        self.branch = branch
        self.scanner_directory_path = scanner_directory_path
        self.repository = repo
        self.dirContent = []
        # The temp directory creation is to handle the repositories with the same name 
        self.temp_dir = str(randrange(100000, 999999))+'_'+self.repo_directory+'/'

    def download(self):
        os.chdir(self.scanner_directory_path)
        while self.downloadRepo:
            git_clone = Popen(['git', 'clone', '--single-branch', '--branch', self.branch, self.git_url, self.temp_dir], stdout=PIPE, stderr=PIPE)
            git_clone_stdout, git_clone_stderr = git_clone.communicate()
            # Temp directory gets created if the path exists -> set the downloadRepoComplete to true to move on 
            # If not, failed to download the repository -> set the downloadRepoComplete to false
            # queueCheck keeps track of the failed jobs 
            if os.path.exists(self.scanner_directory_path+self.temp_dir):
                self.downloadRepo = False
                self.downloadRepoComplete = True
                self.dirContent = glob.glob(self.scanner_directory_path+self.temp_dir+'/*')
                #print("DEBUG - scanner - repository: {}, branch: {}, output: {}, console_output: {}, downloadRepo: {}, scanRepo: {}, dirFileCount: {}".format(repository, branch, str(git_clone_stdout), str(git_clone_stderr), downloadRepo, scanRepo, len(dirContent)))
            elif 'Could not find remote branch' in git_clone_stderr.decode('utf-8'):
                print("INFO - scanner - repository: {}, branch: {}, output: {}, console_output: {}, message: Repo or branch not found".format(self.repository, self.branch, str(git_clone_stdout), str(git_clone_stderr)))
                self.downloadRepo = False
                self.downloadRepoComplete = False
            else:
                self.downloadRepo = True
                self.downloadRepoComplete = False
                self.dirContent = []

        return {'downloadRepoComplete': self.downloadRepoComplete, 'no_of_directories': len(self.dirContent), 'temp_dir': self.temp_dir}