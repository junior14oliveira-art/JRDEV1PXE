import ast, os, sys

errors = []
for root, _, files in os.walk("app"):
    for f in files:
        if not f.endswith(".py"):
            continue
        p = os.path.join(root, f)
        try:
            with open(p, "r", encoding="utf-8") as fh:
                ast.parse(fh.read(), filename=p)
        except SyntaxError as e:
            errors.append((p, str(e)))

if errors:
    print("SYNTAX ERRORS:")
    for path, msg in errors:
        print(f"  {path}: {msg}")
    sys.exit(1)
else:
    print(f"All {sum(1 for r,_,fs in os.walk('app') for f in fs if f.endswith('.py'))} .py files OK")
