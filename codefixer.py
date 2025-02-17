import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import json
import re
import openai
import time

# Your provided functions go here
def get_updated_code_old(prompt):
    """
    Get the updated code from GPT-3 API
    Args: prompt: str
    Returns: str
    """
    # sending request to prompt the GPT-3 API
    print("----- sending request to prompt the GPT-3 API -----")
    start_time = time.time()


    # Set up the OpenAI API credentials openai.
    openai.api_key = "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"
    model_engine = "gpt-3.5-turbo"
    # Set the GPT-3 model engine to use
    # Generate corrected code using GPT-3.5 API
    response = openai.Completion.create(engine=model_engine,
                                        prompt=prompt,
                                        max_tokens=1024,
                                        n=1,
                                        stop=None,
                                        temperature=0.4, )
    end_time = time.time()
    # print the time taken to get the response in seconds
    print("----- Time taken to get the response in seconds: ", end_time - start_time, "-----")
    print("----- Got response from GPT-3 API -----")
    # Extract the corrected code from the response
    corrected_code = response.choices[0].text.strip()
    return corrected_code


import openai

def extract_python_code(text):
    code_pattern = re.compile(r'<code>(.*?)<\/code>', re.DOTALL)
    code_matches = code_pattern.findall(text)

    if code_matches:
        code = ''.join(code_matches)
        return code.replace('\n\n', '\n')
    else:
        return None

def get_updated_code(prompt):
    """
    Get the updated code from GPT-3 API
    Args: prompt: str
    Returns: str
    """

    # Set up the OpenAI API credentials
    openai.api_key = "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"
    model_engine = "gpt-3.5-turbo"

    # Generate corrected code using GPT-3.5 API
    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that takes partial python code and fixes it without changing starting code or ending code. send only code back to user. Don't add code at the end even if its incomplete."},
            {"role": "user", "content": prompt}
        ]
    )

    # Extract the corrected code from the response
    corrected_code = response.choices[0].message.content.strip()
    # extract code inside \n\n use regex
    code_pattern = re.compile(r'```(.*?)```', re.DOTALL)
    code_matches = code_pattern.findall(corrected_code)

    # remove { } from code
    if code_matches:
        code = ''.join(code_matches)
        code = code.replace('\n\n', '\n')
        # remove 'python' from code
        code = code.replace('python', '')
        code = code.replace('{', '')
        code = code.replace('}', '')
        # trim code till 'code:' is found if not found return code
        if 'code:' in code:
            code = code[code.find('code:') + len('code:'):]
        if 'Here' in code:
            # trim from 'Here's' till the fisrt : is found
            code = code[code.find(':') + 1:]

        # if last line starts with pass remove it
        code_in_lines = code.split('\n')
        # pop from  back if linestarts with empty
        for i in range(len(code_in_lines) - 1, -1, -1):
            if code_in_lines[i] == '':
                code_in_lines.pop(i)
            else:
                break
        if code_in_lines[-1].strip().startswith('pass'):
            code_in_lines = code_in_lines[:-1]
        code = '\n'.join(code_in_lines)
        return code
    else:

        code_in_lines = corrected_code.split('\n')
        removed_lines = 0
        for i in range(len(code_in_lines) - 1, -1, -1):
            if code_in_lines[i] == '':
                code_in_lines.pop(i)
                removed_lines += 1
            else:
                break
        if code_in_lines[-1].strip().startswith('pass'):
            code_in_lines = code_in_lines[:-1]
        # add empty lines at the end
        for i in range(removed_lines):
            code_in_lines.append('\n ')
        corrected_code = '\n'.join(code_in_lines)
        if 'Here' in corrected_code:
            # trim from 'Here's' till the fisrt : is found
            corrected_code = corrected_code[corrected_code.find(':') + 1:]

        return corrected_code

def get_sonar_report_data(filename='sonarqube_bugs.json'):
    """
    Get the sonarqube report data from the json file in required format
    Args: filename: str
    Returns: list of dict
    """

    # Open the file and read its contents
    with open(filename, 'r') as file:
        data = json.load(file)
    # Extract the data we want
    all_data = []
    for issue in data['issues']:
        d = {}
        try:
            flow = issue['flows'][0]
            location = flow['locations'][0]
            component = location['component']
            d['file_path'] = "./" + component.split(':')[-1]
            d['start_line'] = location['textRange']['startLine']
            d['end_line'] = location['textRange']['endLine']
            d['message'] = issue['message']
            all_data.append(d)
        except:
            pass
    return all_data

def extract_code_context(file_path, bug_line, context_lines=5):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    start_line = max(bug_line - context_lines - 1, 0)
    end_line = min(bug_line + context_lines, len(lines))

    open_delimiters = {'(', '[', '{'}
    close_delimiters = {')', ']', '}'}
    delimiter_stack = []

    def update_delimiter_stack(line):
        for char in line:
            if char in open_delimiters:
                delimiter_stack.append(char)
            elif char in close_delimiters:
                if delimiter_stack and char == close_delimiters[delimiter_stack[-1]]:
                    delimiter_stack.pop()

    # Adjust the start_line to ensure we don't begin with a partial line
    while start_line > 0:
        current_line = lines[start_line].strip()
        previous_line = lines[start_line - 1].strip()
        update_delimiter_stack(previous_line)
        if not delimiter_stack and (not current_line or current_line[0] not in close_delimiters):
            break
        start_line -= 1

    code_context = lines[start_line:end_line]
    return start_line + 1, ''.join(code_context)



def get_function_or_class_string(file_path, start_line, end_line):
    """
    Get the complete function or class which encloses the bug,
    But limits the search to 10 lines before the start_line and 5 lines after the end_line
    Args: file_path: str
          start_line: int
          end_line: int
    Returns: code: str
             start_index: int
             end_index: int
             start_statement: str
             end_statement: list of str
            start_indent: int
    """

    backward_search_limit = 5
    forward_search_limit = 5
    # Open the file and read its contents
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Search backwards from start_line to find the start of the function or class
    start_index = None
    lines_searched = 0
    for i in range(start_line - 1, max(start_line - backward_search_limit - 1, -1), -1):
        lines_searched += 1
        line = lines[i]
        if line.lstrip().startswith(('def ', 'Class ')):
            start_index = i
            break

    if start_index is None:
        start_index = max(start_line - lines_searched, 0)

    # Search forwards from end_line to find the end of the function or class
    end_index = min(end_line + forward_search_limit, len(lines))

    start_statement = lines[start_index].strip()
    while not start_statement.strip() and start_index < end_index:
        start_statement = lines[start_index].strip()
        start_index += 1


    return ''.join(lines[start_index:end_index+1]), start_index, end_index

def update_line_number(msg, new_line):
    """
    update line number in message according to the new code
    Args: msg: str
          new_line: int
    Returns: str
    """
    pattern = r"(line )(\d+)"
    regex = re.compile(pattern)

    replacement_str = r"\g<1>{}".format(new_line)

    new_text = regex.sub(replacement_str, msg)
    return new_text + f"Line {new_line}"


def write_updated_code_to_file(file_path, code, prev_code=None):
    """
    Write the updated code to the file
    Args: file_path: str
          start_line: int
          end_line: int
          code: str
    Returns: None
    """

    # read the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # remove code from start_line to end_line
    # start_line and end_line are code in the file
    # add a comment in place of start_line saying bug fixed
    print("prev_code :\n", prev_code)
    print('before intentation')
    print("code :\n", code)
    # get the index of code that matches line 1 , and next 2 lines should match line 2 and line 3
    prev_code = prev_code.split('\n')
    start_index = None
    for i in range(len(lines)):
        if lines[i].strip() == prev_code[0].strip()  and lines[i+1].strip() == prev_code[1].strip() and lines[i+2].strip() == prev_code[2].strip():
            start_index = i
            break

    end_index = start_index + len(prev_code) - 1


    # GET THE INDENTATION OF THE start_line is string of code
    start_indent = len(lines[start_index]) - len(lines[start_index].lstrip())
    # add indentation to the comment
    comment = " " * start_indent + "# Bug fixed\n"
    # add indentation to the updated code
    code = code.split('\n')
    code = [" " * start_indent + i for i in code]

    # combine the comment and the updated code
    code = comment + '\n'.join(code)
    # get empty lines from prev_code at the end

    print('after intentation')
    print("code:\n" , code)

    # count the number of empty lines at the end of prev_code
    # it should not count empty lines in the middle of the code
    empty_lines = 0
    for i in range(len(prev_code) - 1, -1, -1):
        if prev_code[i].strip():
            break
        empty_lines += 1

    # add empty lines at the end of the updated code
    code = code + '\n' * empty_lines
    # replace the code with the updated code and retain \n at the end of the line
    lines[start_index:end_index] = [code + '\n' for code in code.split('\n')]
    # write the updated code to the file
    with open(file_path, 'w') as file:
        file.writelines(lines)

    return



import tkinter as tk
from tkinter import ttk
import difflib

class CodeFixerUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Code Fixer")

        # Create the main frame
        self.main_frame = ttk.Frame(self.master, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create the label and text widget for previous code
        self.prev_code_label = ttk.Label(self.main_frame, text="Previous Code:")
        self.prev_code_label.grid(row=0, column=0, sticky=(tk.W, tk.N))
        self.prev_code_text = tk.Text(self.main_frame, wrap=tk.NONE, height=20, width=50)
        self.prev_code_text.grid(row=1, column=0, padx=(0, 10), sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create the label and text widget for updated code
        self.updated_code_label = ttk.Label(self.main_frame, text="Updated Code:")
        self.updated_code_label.grid(row=0, column=1, sticky=(tk.W, tk.N))
        self.updated_code_text = tk.Text(self.main_frame, wrap=tk.NONE, height=20, width=50)
        self.updated_code_text.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create the buttons
        self.ignore_button = ttk.Button(self.main_frame, text="Ignore", command=self.ignore_bug)
        self.ignore_button.grid(row=2, column=0, pady=(10, 0), sticky=(tk.W, tk.E))
        self.fix_button = ttk.Button(self.main_frame, text="Fix", command=self.fix_bug)
        self.fix_button.grid(row=2, column=1, pady=(10, 0), sticky=(tk.W, tk.E))
        self.fix_button = ttk.Button(self.main_frame, text="retry", command=self.retry)
        self.fix_button.grid(row=2, column=2, pady=(10, 0), sticky=(tk.W, tk.E))
        self.diff_button = ttk.Button(self.main_frame, text="Show Diff", command=self.show_diff)
        self.diff_button.grid(row=2, column=3, pady=(10, 0), padx=(10, 0), sticky=(tk.W, tk.E))

        # Configure the column and row weights
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

        # Initialize data and current bug index
        self.data = get_sonar_report_data()
        self.current_bug_index = 0
        self.path = None

        # Load the first bug on application start
        global code_data
        self.code_data = self.process_bug()

    def compare_texts(self):
        content1 = self.prev_code_text.get('1.0', tk.END).splitlines()
        content2 = self.updated_code_text.get('1.0', tk.END).splitlines()

        d = difflib.Differ()
        diff = list(d.compare(content1, content2))

        self.result_text.delete('1.0', tk.END)
        for line in diff:
            if line.startswith('-'):
                self.result_text.insert(tk.END, line[2:] + '\n', 'removed')
            elif line.startswith('+'):
                self.result_text.insert(tk.END, line[2:] + '\n', 'added')
            else:
                self.result_text.insert(tk.END, line[2:] + '\n')

    def show_diff(self):
        self.result_window = tk.Toplevel(self.master)
        self.result_window.title('Comparison Result')
        self.result_text = tk.Text(self.result_window, wrap=tk.NONE)
        self.result_text.pack(fill='both', expand=True)
        self.result_text.tag_configure('added', background='lightgreen')
        self.result_text.tag_configure('removed', background='lightcoral')

        self.compare_texts()

    def retry(self):
        suggested_code = self.code_data[1]
        self.process_bug(suggested_code)
        return


    def ignore_bug(self):
        # Ignore the bug and move to the next bug
        self.current_bug_index += 1
        self.process_bug()
        return

    def fix_bug(self):
        # Fix the bug and move to the next bug
        updated_code = self.code_data[1]
        code = self.code_data[0]
        # add processing txt to in updated window
        self.updated_code_text.delete(1.0, tk.END)
        self.updated_code_text.insert(1.0, 'Processing...')
        write_updated_code_to_file(self.path, updated_code, prev_code=code)
        # add status to the updated window
        self.updated_code_text.delete(1.0, tk.END)
        self.updated_code_text.insert(1.0, 'Fixed')
        self.current_bug_index += 1
        self.process_bug()
        return

    def process_bug(self, wrong_code=None):
        if self.current_bug_index < len(self.data):
            # add fetching message to the both windows
            self.prev_code_text.delete(1.0, tk.END)
            self.prev_code_text.insert(1.0, 'Fetching...')
            self.updated_code_text.delete(1.0, tk.END)
            self.updated_code_text.insert(1.0, 'Fetching...')
            d = self.data[self.current_bug_index]
            self.path = "/Users/SamarthMahendra/draup-server-qa/" + d['file_path'][2:]
            code, start_index, end_index = \
                get_function_or_class_string(self.path, d['start_line'], d['end_line'])
            wrong_suggestion_message = None
            if wrong_code:
                wrong_suggestion_message = """
                last time you sent wrong suggestion 
                suggested code : {wrong_code}
                """
            fix_msg = d['message']
            fix_msg = update_line_number(fix_msg, d['start_line'] - start_index)
            msg = f"""Here's a partial Python code with a bug, please fix the bug without completing the code or adding any new lines of code::
            code:\n{code}
            line number: {d['start_line'] - start_index}
            message: {fix_msg}
            instructions:
            * correct the indentation of before sending the code
            * add pass statement at end the end if its incomplete
            * make only obvious bug fixes

            {str(wrong_suggestion_message)}
            """
            updated_code = get_updated_code(msg) # Display the previous code in the UI
            print("-----old code-----")
            print(code)
            print("-----new code-----")
            print(updated_code)
            temp_prev_code = code.split('\n')
            # get indentation of line 1
            indentation = len(temp_prev_code[0]) - len(temp_prev_code[0].lstrip())
            # remove indentation from all lines
            for i in range(len(temp_prev_code)):
                temp_prev_code[i] = temp_prev_code[i][indentation:]

            temp_new_code = updated_code.split('\n')
            # remove empty lines from start and end
            while temp_new_code[0] == '':
                temp_new_code.pop(0)
            while temp_new_code[-1] == '':
                temp_new_code.pop(-1)
            # get indentation of line 1
            indentation = len(temp_new_code[0]) - len(temp_new_code[0].lstrip())
            # remove indentation from all lines
            for i in range(len(temp_new_code)):
                temp_new_code[i] = temp_new_code[i][indentation:]
            temp_new_code = '\n'.join(temp_new_code)

            temp_prev_code = '\n'.join(temp_prev_code)
            self.prev_code_text.delete(1.0, tk.END)
            self.prev_code_text.insert(tk.END, temp_prev_code)
            # Display the updated code in the UI
            self.updated_code_text.delete(1.0, tk.END)
            self.updated_code_text.insert(tk.END, temp_new_code)
            self.code_data = (code, updated_code)
            return self.code_data
        else:
            # Display a message when there are no more bugs
            self.prev_code_text.delete(1.0, tk.END)
            self.updated_code_text.delete(1.0, tk.END)
            self.prev_code_text.insert(tk.END, "No more bugs to process")
            self.updated_code_text.insert(tk.END, "No more bugs to process")

def main():
    root = tk.Tk()
    app = CodeFixerUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()