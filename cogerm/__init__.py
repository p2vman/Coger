import os
import json
import zipfile
from io import TextIOWrapper

class DynamicObject:
    def __init__(self, attributes):
        for key, value in attributes.items():
            setattr(self, key, value)

    def __repr__(self):
        return f"{self.__class__.__name__}({vars(self)})"

class CogContext:
    def __init__(self, bot, raw, meta):
        self.bot = bot
        self.raw = raw
        if isinstance(meta, DynamicObject):
            self.meta = meta
        else:
            self.meta = DynamicObject(meta)

    def Rew(self, raw):
        return CogContext(self.bot, raw, self.meta)

    def add(self, cog):
        self.bot.add_cog(cog)


class CogLoader:
    def __init__(self, bot):
        self.bot = bot
        self.cog_list = []

    @staticmethod
    def makeasemit(func):
        func.emit = True
        return func

    def emit(self, method: str, *args) -> None:
        for obj in self.cog_list:
            if hasattr(obj, method):
                func = getattr(obj, method)
                if hasattr(func, 'emit'):
                    func(*args)

    def load(self, source: str, meta) -> None:
        if source.endswith(".zip"):
            self.load_from_zip(source, meta)
        else:
            self.load_from_directory(source, meta)

    def load_from_directory(self, dir_: str, meta) -> None:
        base_ctx = CogContext(self.bot, {}, meta)

        for filename in os.listdir(dir_):
            file_path = os.path.join(dir_, filename)

            if filename.endswith("_c.py"):
                self.load_cog_from_python(file_path, base_ctx)
            elif filename.endswith("cog.json"):
                self.load_cog_from_json(file_path, base_ctx)

    def load_from_zip(self, zip_path: str, meta) -> None:
        base_ctx = CogContext(self.bot, {}, meta)

        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            for filename in zip_file.namelist():
                if filename.endswith("_c.py"):
                    with zip_file.open(filename) as file:
                        self.load_cog_from_python(TextIOWrapper(file, encoding='utf-8'), base_ctx, filename)
                elif filename.endswith("cog.json"):
                    with zip_file.open(filename) as file:
                        self.load_cog_from_json(TextIOWrapper(file, encoding='utf-8'), base_ctx)

    def load_cog_from_python(self, file, base_ctx, file_name=None):
        if isinstance(file, str):
            with open(file, 'r', encoding='utf-8') as f:
                code = f.read()
        else:
            code = file.read()

        namespace = {}
        exec(code, namespace)
        class_dict = {name: obj for name, obj in namespace.items() if isinstance(obj, type)}
        func_dict = {name: obj for name, obj in namespace.items() if callable(obj)}

        json_filepath = (file[:-5] + ".json") if isinstance(file, str) else (file_name[:-5] + ".json")
        if os.path.exists(json_filepath):
            with open(json_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.process_entries(data, base_ctx, class_dict, func_dict)
        elif file_name and file_name[:-5] in class_dict:
            class_dict[file_name[:-5]](base_ctx).init(base_ctx)

    def load_cog_from_json(self, file, base_ctx):
        data = json.load(file)
        for cog_name, cog_info in data.items():
            cog_file_path = cog_name if isinstance(file, str) else os.path.join(os.path.dirname(file.name), cog_name)
            if os.path.exists(cog_file_path):
                print(f"Load {cog_info['name']}")
                with open(cog_file_path, 'r', encoding='utf-8') as f:
                    namespace = {}
                    exec(f.read(), namespace)
                    class_dict = {name: obj for name, obj in namespace.items() if isinstance(obj, type)}
                    func_dict = {name: obj for name, obj in namespace.items() if callable(obj)}

                    self.process_entries(cog_info['entries'], base_ctx, class_dict, func_dict)

    def process_entries(self, entries, base_ctx, class_dict, func_dict):
        for entry in entries:
            ctx = base_ctx.Rew(entry['raw']) if 'raw' in entry else base_ctx

            if entry['name'] in func_dict and entry.get('type') == 0:
                func_dict[entry['name']](ctx)
            elif entry['name'] in class_dict:
                ins = class_dict[entry['name']](ctx)
                self.cog_list.append(ins)
                if entry.get('load'):
                    ctx.add(ins)
                ins.init(ctx)
