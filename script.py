from string import Template


def vite_js():
    # 本地开发修改路径为 ./vue-project/dist/assets
    # with open('./vue-project/dist/assets/main.js', 'r') as file:
    with open('.package/assets/main.js', 'r') as file:
        vite_js = file.read().replace('\n', '')
        return Template('''
    () => {
      $vite_js
    }
  ''').substitute(vite_js=vite_js)
