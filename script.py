from string import Template

def vite_js():
  with open('./vue-project/dist/assets/main.js', 'r') as file:
    vite_js = file.read().replace('\n', '')
    return Template('''
    () => {
      $vite_js
    }
  ''').substitute(vite_js = vite_js)