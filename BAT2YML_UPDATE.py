import tkinter as tk
from tkinter import filedialog,messagebox
import zipfile,re
from pathlib import Path

class App:
    def __init__(self,root):
        self.root=root
        self.bats={}
        self.pyfiles=[]

        left=tk.Frame(root)
        left.pack(side='left',fill='y')
        right=tk.Frame(root)
        right.pack(side='right',fill='both',expand=True)

        tk.Button(left,text='ZIPを開く',command=self.open_zip).pack(fill='x')
        self.list=tk.Listbox(left,width=40)
        self.list.pack(fill='both',expand=True)
        self.list.bind('<<ListboxSelect>>',self.select_bat)

        self.info=tk.Label(left,text='ZIPを選択')
        self.info.pack(fill='x')

        self.txt=tk.Text(right)
        self.txt.pack(fill='both',expand=True)

        tk.Button(right,text='YAMLコピー',command=self.copy_yaml).pack(fill='x')

    def open_zip(self):
        f=filedialog.askopenfilename(filetypes=[('ZIP','*.zip')])
        if not f:return
        self.load_zip(f)

    def load_zip(self,f):
        self.bats={}
        self.pyfiles=[]
        self.list.delete(0,tk.END)
        with zipfile.ZipFile(f) as z:
            for n in z.namelist():
                if n.lower().endswith('.bat'):
                    self.bats[Path(n).name]=z.read(n).decode('utf-8','ignore')
                if n.lower().endswith('.py'):
                    self.pyfiles.append(Path(n).name)
        for k in self.bats:self.list.insert(tk.END,k)
        self.info.config(text=f'BAT:{len(self.bats)} PY:{len(self.pyfiles)}')

    def select_bat(self,e):
        s=self.list.curselection()
        if not s:return
        name=self.list.get(s[0])
        yml=self.convert(self.bats[name],Path(name).stem)
        self.txt.delete('1.0',tk.END)
        self.txt.insert('1.0',yml)

    def copy_yaml(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.txt.get('1.0',tk.END))
        messagebox.showinfo('完了','クリップボードへコピーしました')

    def convert(self,bat,name):
        steps=['      - uses: actions/checkout@v4']
        if 'pyinstaller' in bat.lower():
            
steps += [
"""      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
""",
"""      - name: Install PyInstaller
        run: pip install pyinstaller
"""
]

        py_target=None
        m=re.search(r'pyinstaller.*?([A-Za-z0-9_\/.-]+\.py)',bat,re.I)
        if m:
            py_target=Path(m.group(1)).name
            if py_target not in self.pyfiles and len(self.pyfiles)==1:
                bat=bat.replace(m.group(1),self.pyfiles[0])

        for line in bat.splitlines():
            l=line.strip()
            if not l or l.startswith('@echo') or l.lower()=='pause':
                continue
            if 'where pyinstaller' in l.lower():
                continue
            steps.append(f'      - name: Command\n        shell: cmd\n        run: |\n          {l}')

        return f'name: {name}\n\non:\n  workflow_dispatch:\n\njobs:\n  build:\n    runs-on: windows-latest\n\n    steps:\n'+'\n'.join(steps)

root=tk.Tk()
root.title('BAT -> GitHub Actions YML')
root.geometry('1200x700')
App(root)
root.mainloop()
