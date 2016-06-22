def test_oauth_auth_example():
    import ast
    import _ast
    import codegen

    client_id = "n4mnzQGfDEfOhFixwBvLV2mZJJLvf86pzfMMiPF5"
    client_secret = "40ON9IPJRDAngUkVbGBTEjCBAwc2wB7lV8e71jJUPKabdKq6KBTUBKb1xGkh82KtAI1AqISrL3Zi4sTfhCBVh27YvlV6Y5klpXXV5loUWvuhMSRiN3HRZzVDO0fLBibv"

    with open("examples/oauth_auth_example.py", "r") as f:
        data = f.read()
        p = ast.parse(data)
    for node in p.body:
        if type(node) == _ast.Assign:
            if node.targets[0].id == 'client_id':
                node.value.s = client_id
            if node.targets[0].id == 'client_secret':
                node.value.s = client_secret
    ls = {}
    exec(codegen.to_source(p), ls)
    assert ls['course']['courses'][0]['id'] == 67
