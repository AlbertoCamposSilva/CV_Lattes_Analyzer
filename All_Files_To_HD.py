from Lattes import Lattes
from Lattes import Lattes
import os, glob

num = 0
ids_em_JSON = [y[y.find('Lattes_')+7:-4] for x in os.walk('D:/Lattes/Lattes_ZIP') for y in glob.glob(os.path.join(x[0], '*.JSON'))]
for x in os.walk('D:/Lattes/Lattes_ZIP'):
    for y in glob.glob(os.path.join(x[0], '*.zip')):
        print(f'Importing file {y}')
        try:
            lattes = Lattes()
            lattes.id = y[-20:-4]
            if lattes.id not in ids_em_JSON:
                lattes.read_zip_from_disk(filename = y)
                lattes.get_xml()
                lattes.save_xml_to_disk(replace = False)
                lattes.save_json_to_disk(replace = False)
                print(f'Saved id {lattes.id} to disk.')
        except:
            with open('d:/erros.txt', 'a') as file:
                file.write(y + '\n')