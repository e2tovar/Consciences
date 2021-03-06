"""
Seguir estructura del código

-1º. Leemos el fichero CSV que se corresponde con el archivo salida de Aquiles.
-2º. Obtenemos las columnas: "Tipo Evento", "Contenido" e "Imagen".
-3º. Eliminamos, de esas columnas, todas las filas cuyo "Contenido" o "Tipo Evento" sea vacío  o "Tipo Evento" no sea
     "Cursor" excepto para las que contengan en la columna "Contenido" un string o substring "{ctrl}k{ctrl}k". De esta
     forma nos quedamos solo con los "Tipo Evento" --> Cursor y con los "Tipo Evento" --> Keystrokes cuyo "Contenido"
     contenga un string o substring "{ctrl}k{ctrl}k", es decir, se haya detectado que el analista quiere que se aprenda
     a partir de ese momento hasta la siguiente vez que se encuentra "{ctrl}k{ctrl}k".
     Esto se deberá modificar cuando tengamos una versión en la que necesitemos recoger keystrokes diferentes.
-4º. Se crea, a partir de las columnas filtradas anteriormente, un DataFrame para poder trabajar con él.
-5º. Se recogen la lista de acciones que se han realizado entre una un "{ctrl}k{ctrl}k" y otro "{ctrl}k{ctrl}k".
-6º. Se recoge, a partir del nombre de la imagen, el grupo de la imagen para la fase de entrenamiento (aprendizaje).
     Hay que tener en cuenta que cada acción puede tener asociado una imagen diferente (esa información está en el log
     de aquiles). En ese caso, para esa imagen hay que buscarle al grupo que pertenece (esto se hace asociando los ids
     (nombre de la imagen) de los archivos image_match (que es el log enriquecido) y del log de aquiles).
     Se debe retornar algo así por cada acción:
     [Posición 0 --> 0 si "Tipo Evento" es Cursor y 1 si es Keystrokes,
     Posición 1 --> (A partir de "Contenido") 0 si es click izquierdo ,1 si es click derecho o "la cadena string" si
     es Keystrokes,
     Posición 2 --> Primera coordenada,
     Posición 3 --> Segunda coordenada,
     Posición 4 --> Grupo de la imagen de la fila del contenido en la que está. Si esa fila no tiene imagen asociada,
     se utilizará el grupo de la imagen anterior]
-7º. Se transforman todas las acciones(por acción) en un formato adecuado. El formato para
     las acciones debe quedar:
     [tipo_de_click, coordenada x, coordenada y, grupo]
     El tipo_de_click será 0 si es "{LEFT MOUSE}" y 1 si es "{RIGHT MOUSE}".
     Así, el array resultante podría quedar así: [0,450,354,4] siendo el último elemento el grupo.
     Esta función es útil para manejar versiones del código. Así, para las versiones del código en las que necesitemos
     un tipo de información diferente, podemos modificar esta función y recoger lo que necesitemos.
-8º. Creación de los datos de entrenamiento con los labels (etiquetas):
     Crear una lista de listas (A) que contenga las entradas y salidas del conjunto de entrenamiento.
     La entrada (a) tiene la forma del paso anterior. La salida(b) es la siguiente acción del log de aquiles con esta
     forma: [1,451,355], siendo el primer elemento el tipo de click, el segundo la coordenada x y el tercer elemento la
     coordenada y.
     Para la siguiente posición del array, (b) será la entrada y la salida de esa entrada será la siguiente acción
     del log de aquiles y así sucesivamente hasta que se encuentre el siguiente fin de aprendizaje
     (end_event_learning_capture).
     Un ejemplo de esto podría ser:
     [[[0,450,354,grupo], [1,451,355]], [[1,451,355,grupo],[0,349,567]], (...)] --> Conjunto de acciones divididas entre
     sus entradas y salidas(labels). Esto servirá para el entrenamiento y testeo de la red.
-9º. Una función que se llama "get_batch" que recibe por parámetro el array del anterior y un número entero y
     devuelva un número de elementos de ese array (batches) igual al número entero dado. Además, debe existir una
     variable que guarde el índice en el que está. Si tenemos un array de 1000 elementos y cogemos 50 ( la primera vez
     que se llama a la función), cada vez que se llame a esa función, debe dar los siguientes 50 elementos
     (tener en cuenta las ventanas temporales).

@(sara.moreno)
@(gabriel.vazquez)
"""
# pip3 install pandas
import pandas as pd
# Para instalar tensorflow (versión CPU): Una vez tengáis Python versión > 3 --> poner en línea de comandos:
# pip3 install --upgrade tensorflow
# Para versión GPU:
# pip3 install --upgrade tensorflow-gpu
import tensorflow as tf
import numpy as np

# Keystrokes a tener en cuenta
start_event_learning_capture = "{ctrl}k{ctrl}k"
end_event_learning_capture = "{ctrl}k{ctrl}k"

"""
Funciones útiles
"""

def numpy_fillna(data):
    """
    Esta función convierte todos los elementos en un array del mismo tamaño cada uno con ceros si faltan elementos.
    :param data:
    :return:
    """

    # Get lengths of each row of data
    lens = np.array([len(i) for i in data])

    # Mask of valid places in each row
    mask = np.arange(lens.max()) < lens[:,None]

    # Setup output array and put elements from data into masked positions
    out = np.zeros(mask.shape, dtype=data.dtype)
    out[mask] = np.concatenate(data)
    return out

def pt(title=None, text=None):
    """
    Use the print function to print a title and an object coverted to string
    :param title:
    :param text:
    """
    if text is None:
        text = title
        title = "-----------------------------"
    else:
        title += ':'
    print(str(title) + " \n " + str(text))

def initialize_session():
    """
    Initialize interactive session and all local and global variables
    :return: Session
    """
    sess = tf.InteractiveSession()
    sess.run(tf.local_variables_initializer())
    sess.run(tf.global_variables_initializer())
    return sess

def split_list_in_pairs (a_list):
    """
    A partir de una lista tal que "a_list" = [1,2,3,4,5,6,7], devuelve otra lista que contenga listas de elementos 2 a 2
    excepto si es impar que devolverá el último elemento en una lista propia.
    E.g.: de "a_list" devuelve --> [[1,2],[3,4],[5,6],[7]]
    """
    if len(a_list) == 1 or not a_list:
        final_list = [a_list]
    else:
        final_list = [a_list[i:i + 2] for i in range(0, len(a_list), 2)]
    return final_list
"""
PASOS
"""
# Paso 1º. Ruta del fichero
def read_file(name_file, separator):
    """
    Lee el fichero csv pasado como path
    """
    file = pd.read_csv(name_file, sep=separator)
    return file

# Paso 2º. Obtenemos las columnas: "Tipo Evento", "Contenido" e "Imagen"
def get_columns(file):
    """
    Se recogen las columnas "tipo_evento", "contenido" y "imagen" y se retornan
    """
    tipo_evento = file.pop("Tipo Evento")
    contenido = file.pop("Contenido")
    imagen = file.pop(" Imagen")
    return tipo_evento,contenido,imagen

# Paso 3 y 4
def normalize_columns_and_create_dataframe(tipo_evento, contenido, imagen):
    """
    Paso 3. Eliminamos, de esas columnas, todas las filas cuyo "Contenido" o "Tipo Evento" sea vacío  o "Tipo Evento" no
    sea "Cursor" excepto para las que contengan en la columna "Contenido" un string o substring "{ctrl}k{ctrl}k". De
    esta forma nos quedamos solo con los "Tipo Evento" --> Cursor y con los "Tipo Evento" --> Keystrokes cuyo
    "Contenido" contenga un string o substring "{ctrl}k{ctrl}k", es decir, se haya detectado que el analista quiere que
    se aprenda a partir de ese momento hasta la siguiente vez que se encuentra "{ctrl}k{ctrl}k".
    Paso 4. Se crea, a partir de las columnas filtradas anteriormente, un DataFrame para poder trabajar con él y se
    retorna.
    """
    # Paso 3
    # TODO (@IWT2) No eliminar elementos que contengan información relevante (para futuras versiones)
    for index in range(0, len(tipo_evento)):
        if (not tipo_evento[index] == "Cursor" or contenido[index] == "NaN" or contenido[index] == "") \
                and start_event_learning_capture not in contenido[index].lower():
            del tipo_evento[index]
            del contenido[index]
            del imagen[index]
    # Paso 4
    dataset = {}
    dataset[0] = tipo_evento
    dataset[1] = contenido
    dataset[2] = imagen
    final_dataframe = pd.DataFrame(data=dataset)
    final_dataframe.columns = ['Tipo Evento', 'Contenido', 'Imagen']
    print(final_dataframe)
    return final_dataframe

# Paso 5. Obtenemos las imágenes a partir de los keystrokes y array de lista de acciones (índices)
def get_images_from_keystrokes(tipo_evento, imagen):
    """
    Se recogen la lista de acciones que se han realizado entre una un "start_event_learning_capture" y otro
    "end_event_learning_capture".
    """
    # TODO images_from_keystrokes, por ahora, solo contiene los ids de las imágenes de las filas que tienen "keystrokes"
    # TODO en su tipo_evento. ¿Debe contener todas las imágenes de todas las acciones que hay en starts_ends_indexes?
    # TODO Si no es ahora, esa información la debemos tener en la siguiente fase.
    images_from_keystrokes = []  # Nombre de imágenes para utilizarlos como ids en el excel
    # Obtenemos los índices de las filas con "Tipo Evento" --> Keystrokes
    keystrokes_indexes = [x for x in range(len(list(tipo_evento.values))) if list(tipo_evento.values)[x].lower() ==
                          "keystrokes"]
    starts_ends_indexes = split_list_in_pairs(
        a_list=keystrokes_indexes)  # Lista de parejas de todos los keystrokes_indexes
    print("keystrokes_indexes", keystrokes_indexes)
    print("index_in_pairs", starts_ends_indexes)
    for index in keystrokes_indexes:
        images_from_keystrokes.append(list(imagen.values)[index])
    print("images_from_keystrokes", images_from_keystrokes)
    return images_from_keystrokes, starts_ends_indexes

# Paso 6. Obtenemos las siguientes acciones a realizar a partir de los índices obtenidos previamente.
# Se debe acceder al excel image_match con los ids de las imagenes para recoger el grupo de cada una de ellas.
def get_next_actions(contenido, images_from_keystrokes, starts_ends_indexes):
    next_actions = []  # Lista de listas de siguientes acciones. Cada lista contenida tiene el siguiente formato:
    # [Posición 0 --> 0 si "Tipo Evento" es Cursor y 1 si es Keystrokes,
    # Posición 1 --> (A partir de "Contenido") 0 si es click izquierdo ,1 si es click derecho o "la cadena string" si
    # es Keystrokes,
    # Posición 2 --> Primera coordenada,
    # Posición 3 --> Segunda coordenada,
    # Posición 4 --> Grupo de la imagen de la fila del contenido en la que está. Si esa fila no tiene imagen asociada,
    # se utilizará el grupo de la imagen anterior]
    # TODO Tener en cuenta el doc del archivo para realizar esta función
    if not starts_ends_indexes:
        next_actions = -1  # No hay siguientes acciones
    else:
        for index in range(len(starts_ends_indexes)):
            actual_learning = starts_ends_indexes[index]  # Contiene una lista con un número o un par de números
            if (len(actual_learning)) == 2:
                # TODO (@IWT2) Finish: Recoger la lista de elementos que hay entre los dos índices
                # TODO utilizar images_from_keystrokes para recoger las imagenes del excel image_match.
                for element_index in range(actual_learning[0],actual_learning[1]):
                    next_actions.append([contenido[element_index]])
            else: # Solo tiene un elemento
                pass  # No recogemos nada (en esta versión)
    print("next_actions",next_actions)
    return next_actions
# Paso 7
def normalize_actions(next_actions):
    # TODO

    return []
# Paso 8
def create_batches(normalized_actions):
    # TODO
    return []

# Paso 9
def get_batch(batches, quantity):
    global index_batch  # Para tener en cuenta el índice por donde va el recorrido del batch.
    # Si quantity es None, que recoja un número por defecto.
    # TODO
    return[]

index_batch = 0  # Índice para tener en cuenta el índice por donde va el recorrido del batch.
batches = []  # Que se utilizará para quedar guardada la primera vez que se cree.
file_aquiles = "C:\\Users\Gabriel\Desktop\\02. Aquiles\dist Aquiles 20171113\\20180123\logfiles20180123.csv"  # Se deberá
file_mod2_3 = "log2_3"  # Se deberá
# recoger como parámetro al igual que quantity y start_all_flag

def main_train_phase(file_path_aquiles=None, file_path_mod2_3=None, quantity=None, start_all_flag=False):
    """
    Este método realiza todos las fases para retornar un batch de tamaño "quantity".
    Si "start_all_flag" es False, realiza todos los pasos para crear el batch y guardarlo en memoria. Una vez que ese
    batch con todos los elementos esté creado (la primera vez o cuando se crea necesario realizarlo), se debe poner a
    False para solo retornar el batch de tamaño "quantity". Al realizar todos los pasos se actualiza la variable global
    "batches".
    Si en alguna de las fases se retorna un elemento vacío, el método mostrará por pantalla que no existen acciones a
    realizar y el elemento batches será un array vacío por lo que retornará un array vacío.
    """
    global batches
    if start_all_flag:
        # TODO Tras el cambio en la forma de realizar la fase de entrenamiento (ahora es por el grupo), es posible que
        # TODO los nombres de las variables y las entradas de las funciones no sean acordes al doc del archivo.
        # TODO Cambiarlo si es necesario e intentar hacer el código para que sea granular.
        file = read_file(name_file=file_path_aquiles,separator=";")
        tipo_evento, contenido, imagen = get_columns(file=file)
        normalize_columns_and_create_dataframe(tipo_evento=tipo_evento,contenido=contenido,imagen=imagen)
        images_from_keystrokes, starts_ends_indexes = get_images_from_keystrokes(tipo_evento=tipo_evento, imagen=imagen)
        next_actions = get_next_actions(contenido=contenido, images_from_keystrokes=images_from_keystrokes,
                                        starts_ends_indexes=starts_ends_indexes)
        if not next_actions == -1:
            normalized_actions = normalize_actions(next_actions=next_actions)
            batches = create_batches(normalized_actions)
        else:
            pt("No hay acciones")
    batch_to_train = get_batch(batches=batches,quantity=quantity)
    return batch_to_train

# Get batch algorithm
#batch = main_train_phase(file_aquiles, file_mod2_3,2, True)

"""
RED NEURONAL
"""
# input con label
# Creación del conjunto de entrenamiento
# Como se utiliza "mean_squared_error" para el cálculo del error, se estipula que 0 es click izquierdo y 100 click
# derecho. Así, el error absoluto buscará mejor de una forma más certera.
tipo_click = 0.
coordenada_x = 0.
coordenada_y = 0.
grupo = 0.

input_batch = []
label_batch = []

for int in range(10):
    if int % 2 == 0:
        tipo_click = 0.
    else:
        tipo_click = 100.
    coordenada_x+= 100.
    coordenada_y+= 100.
    grupo += 1
    input_batch.append([tipo_click,coordenada_x,coordenada_y,grupo])
    label_batch.append([tipo_click,coordenada_x,coordenada_y])

inputs = np.asarray(input_batch).reshape(10,4)
labels = np.asarray(label_batch).reshape(10,3)

pt("inputs",inputs)
pt("labels",labels)

# Parametros de la red
n_oculta_1 = 8 # 1ra capa de atributos
n_oculta_2 = 8 # 2ra capa de atributos
n_entradas = 4 # 4 datos de entrada
n_clases = 3 # 3 salidas

# input para los grafos
x = tf.placeholder(tf.float32, [None, n_entradas],  name='DatosEntrada')
y = tf.placeholder(tf.float32, [None, n_clases], name='Clases')

# Creamos el modelo
def perceptron_multicapa(x, pesos, sesgo):
    # Función de activación de la capa escondida
    capa_1 = tf.add(tf.matmul(x, pesos['h1']), sesgo['b1'])
    # activacion relu
    capa_1 = tf.nn.relu(capa_1)
    # Función de activación de la capa escondida
    capa_2 = tf.add(tf.matmul(capa_1, pesos['h2']), sesgo['b2'])
    # activación relu
    capa_2 = tf.nn.relu(capa_2)
    # Salida con activación lineal
    salida = tf.matmul(capa_2, pesos['out']) + sesgo['out']
    return salida


# Definimos los pesos y sesgo de cada capa.
pesos = {
    'h1': tf.Variable(tf.random_normal([n_entradas, n_oculta_1])),
    'h2': tf.Variable(tf.random_normal([n_oculta_1, n_oculta_2])),
    'out': tf.Variable(tf.random_normal([n_oculta_2, n_clases]))
}
sesgo = {
    'b1': tf.Variable(tf.random_normal([n_oculta_1])),
    'b2': tf.Variable(tf.random_normal([n_oculta_2])),
    'out': tf.Variable(tf.random_normal([n_clases]))
}


# Construimos el modelo
pred = perceptron_multicapa(x, pesos, sesgo)

# Definimos la funcion de coste
#costo = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=pred, labels=y))
error = tf.losses.mean_squared_error(labels=y,predictions=pred)
# Algoritmo de optimización
optimizar = tf.train.AdamOptimizer(learning_rate=0.001).minimize(error)

# Evaluar el modelo
#pred_correcta = tf.equal(tf.argmax(pred, 1), tf.argmax(y, 1))
# Calcular la precisión
#acierto = tf.subtract(tf.constant(1.),error)

sess = initialize_session()

epochs = 100
trains = 10
costes = []
precisiones = []
stop_train_flag = False
# Entrenamiento
for epoca in range(10000):
    if stop_train_flag:
        break
    for train in range(trains):
        #pt("batches_[train][0].shape",batches_[train][0].shape)
        x_train, y_train = inputs, labels
        # Optimización por backprop y funcion de costo
        _, actual_error, y_ = sess.run([optimizar, error,pred],
                                 feed_dict={x: x_train[train].reshape(1,4), y: y_train[train].reshape(1,3)})
        if train == 0:
            pt("error",actual_error)
            costes.append(actual_error)
            #precisiones.append(accuracy)
            pt("y", y_)
        if actual_error < 0.0000001:
            stop_train_flag = True
            break
    # imprimir información de entrenamiento
    if epoca % 1 == 0:
        pass
        #pt("costes",costes)
        #pt("precisiones",precisiones)

pt("costes", costes)
pt("FINAL para 10000 épocas con 10 entrenamientos cada una. Debe salir:", labels[0])
pt("Y la salida es:",pred.eval(feed_dict={x:inputs[0].reshape(1,4)}))
pt("Con un error de:", costes[-1])
#np.savetxt("W.csv", W_val, delimiter=",")
#np.savetxt("b.csv", b_val, delimiter=",")