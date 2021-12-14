import sys
import subprocess
import re
import tempfile

# Usage
if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} [module_name] [library_dir]")
    exit(-1)

MODULE_NAME = sys.argv[1]
DIRECTORY = sys.argv[2]

print(f'Generating stubs for module: {MODULE_NAME} in directory: {DIRECTORY}')

try:

    # Create stubs, add PYTHONPATH to find the build module
    # CWD to to extdir where the built module can be found to extract the types
    subprocess.check_call(['stubgen', '-p', MODULE_NAME, '-o', f'{DIRECTORY}'], cwd=DIRECTORY)

    # Add py.typed
    open(f'{DIRECTORY}/depthai/py.typed', 'a').close()

    # imports and overloads
    with open(f'{DIRECTORY}/depthai/__init__.pyi' ,'r+') as file:
        # Read
        contents = file.read()

        # Add imports
        stubs_import = 'import depthai.node as node\nimport typing\nimport json\n' + contents
        # Create 'create' overloads
        nodes = re.findall('def \S*\(self\) -> node.(\S*):', stubs_import)
        overloads = ''
        for node in nodes:
            overloads = overloads + f'\\1@overload\\1def create(self, arg0: typing.Type[node.{node}]) -> node.{node}: ...'
        #print(f'{overloads}')
        final_stubs = re.sub(r"([\s]*)def create\(self, arg0: object\) -> Node: ...", f'{overloads}', stubs_import)

        # Writeout changes
        file.seek(0)
        file.write(final_stubs)

    # Flush previous stdout
    sys.stdout.flush()

    # Check syntax
    with tempfile.NamedTemporaryFile() as config:
        config.write('[mypy]\nignore_errors = True\n'.encode())
        config.flush()
        subprocess.check_call([sys.executable, '-m' 'mypy', f'{DIRECTORY}/{MODULE_NAME}', f'--config-file={config.name}'])

except subprocess.CalledProcessError as err:
    exit(err.returncode)

exit(0)