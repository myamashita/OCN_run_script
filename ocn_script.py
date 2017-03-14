import sublime
import sublime_plugin
import os
import sys
import subprocess
import locale

if os.name == 'nt':
    try:
        import _winreg
    except (ImportError):
        import winreg as _winreg
    from ctypes import windll, create_unicode_buffer

class NotFoundError(Exception):
    pass

if sys.version_info >= (3,):
    installed_dir, _ = __name__.split('.')
else:
    installed_dir = os.path.basename(os.getcwd())

def get_setting(key, default=None):
    settings = sublime.load_settings('OCN_run_script.sublime-settings')
    os_specific_settings = {}
    return os_specific_settings.get(key, settings.get(key, default))

DEFAULT_CONTENT = """[
    {   // Define your custom Script here
        // Name to show in Command Palette
        "caption": "File: New",
        // Command to invoke
        "command": "new_file",
        // script to run
        "args": {"script": ["value"]}
    }
]"""
DEFAULT_PROMPT = """{// Define your custom Prompt here
        "prompt": "",
}"""

class TerminalSelector():
    default = None

    @staticmethod
    def get():
        package_dir = os.path.join(sublime.packages_path(), installed_dir)
        terminal = get_setting('prompt')
        if terminal:
            dir, executable = os.path.split(terminal)
            return terminal

        default = None

        if os.name == 'nt':
            default = os.environ['SYSTEMROOT'] + '\\System32\\cmd.exe'
        TerminalSelector.default = default
        return default

class TerminalCommand():
    def run_script(self, dir_, parameters):
        try:
            for k, v in enumerate(parameters):
                parameters[k] = v.replace('%CWD%', dir_)
            args = [TerminalSelector.get()]
            args.extend(parameters)
            encoding = locale.getpreferredencoding(do_setlocale=True)
            if sys.version_info >= (3,):
                cwd = dir_
            else:
                cwd = dir_.encode(encoding)
            # Copy over environment settings onto parent environment
            env_setting = get_setting('env', {})
            env = os.environ.copy()
            for k in env_setting:
                if env_setting[k] is None:
                    env.pop(k, None)
                else:
                    env[k] = env_setting[k]

            # Normalize environment settings for ST2
            # https://github.com/wbond/sublime_terminal/issues/154
            # http://stackoverflow.com/a/4987414
            for k in env:
                if not isinstance(env[k], str):
                    if isinstance(env[k], unicode):
                        env[k] = env[k].encode('utf8')
                    else:
                        print('Unsupported environment variable type. Expected "str" or "unicode"', env[k])
            # Run our process
            subprocess.Popen(args, cwd=cwd, env=env)

        except (OSError) as exception:
            print(str(exception))
            sublime.error_message('Terminal: The terminal ' +
                TerminalSelector.get() + ' was not found')
        except (Exception) as exception:
            sublime.error_message('Terminal: ' + str(exception))


class OpenScriptCommand(sublime_plugin.WindowCommand, TerminalCommand):
    def run(self, paths=[], script=None):
        path = sublime.packages_path()
        self.run_script(path, script)

class EditPromptUserCommand(sublime_plugin.WindowCommand):
    def run(self):
        """Open `Packages/User/OCN_run_script.sublime-settings` for custom definitions"""
        filepath = os.path.join(sublime.packages_path(), 'User\OCN_run_script.sublime-settings')
        if not os.path.isfile(filepath):
            with open(filepath, 'w') as f:
                f.write(DEFAULT_PROMPT)

        # Open the commands file
        self.window.run_command('open_file', {
            'file': filepath,
        })

class EditScriptUserCommand(sublime_plugin.WindowCommand):
    def run(self):
        """Open `Packages/User/Default.sublime-commands` for custom definitions"""
        filepath = os.path.join(sublime.packages_path(), 'User\OCN_run_script.sublime-commands')
        if not os.path.isfile(filepath):
            with open(filepath, 'w') as f:
                f.write(DEFAULT_CONTENT)

        # Open the commands file
        self.window.run_command('open_file', {
            'file': filepath,
        })
