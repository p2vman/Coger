import os
import json

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

    def load(self, dir_: str, meta):
        base_ctx = CogContext(self.bot, {}, meta)

        for filename in os.listdir(dir_):
            file_path = os.path.join(dir_, filename)

            if filename.endswith("_c.py"):
                self.load_cog_from_python(file_path, base_ctx)
            elif filename.endswith("cog.json"):
                self.load_cog_from_json(file_path, base_ctx)

    def load_cog_from_python(self, file_path, base_ctx):
        with open(file_path, 'r', encoding='utf-8') as file:
            namespace = {}
            exec(file.read(), namespace)
            class_dict = {name: obj for name, obj in namespace.items() if isinstance(obj, type)}
            func_dict = {name: obj for name, obj in namespace.items() if callable(obj)}

            json_filepath = file_path[:-5] + ".json"
            if os.path.exists(json_filepath):
                with open(json_filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.process_entries(data, base_ctx, class_dict, func_dict)
            elif file_path[:-5] in class_dict:
                class_dict[file_path[:-5]](base_ctx).init(base_ctx)

    def load_cog_from_json(self, json_path, base_ctx):
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for cog_name, cog_info in data.items():
                cog_file_path = os.path.join(os.path.dirname(json_path), cog_name)
                if os.path.exists(cog_file_path):
                    print(f"Load {cog_info['name']}")
                    with open(cog_file_path, 'r', encoding='utf-8') as file:
                        namespace = {}
                        exec(file.read(), namespace)
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
                if entry.get('load'):
                    ctx.add(ins)
                ins.init(ctx)