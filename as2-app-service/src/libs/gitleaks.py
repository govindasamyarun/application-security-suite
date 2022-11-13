import shutil, re, json
from subprocess import Popen, PIPE

class Gitleaks():
    def __init__(self, gitleaks_path, scanner_directory, branch, temp_dir):
        self.gitleaks_path = gitleaks_path
        self.scanner_directory = scanner_directory
        self.branch = branch
        self.temp_dir = temp_dir

    def scan(self):
        scanner = Popen([self.gitleaks_path, 'detect', '--source', self.temp_dir, '-v', '--log-opts='+self.branch], stdout=PIPE, stderr=PIPE)
        scanner_stdout, scanner_stderr = scanner.communicate()
        scanner_stdout = scanner_stdout.decode('UTF-8')
        scanner_stdout = scanner_stdout.replace('\n', '')
        scanner_stdout = scanner_stdout.replace('\t', '')
        scanner_parsed_data = re.findall(r'(.*?)\"\}', scanner_stdout)
        scanner_output = []
        # Removes the temp directory and its contents 
        shutil.rmtree(self.scanner_directory+self.temp_dir, ignore_errors=True)
        if len(scanner_parsed_data) != 0:
            for j in range(len(scanner_parsed_data)):
                try:
                    scanner_output.append(json.loads(scanner_parsed_data[j] + '"}'))
                except:
                    continue

        # Execute process_scanner_output function 
        return {"length": len(scanner_parsed_data), "branch": self.branch, "values": scanner_output}