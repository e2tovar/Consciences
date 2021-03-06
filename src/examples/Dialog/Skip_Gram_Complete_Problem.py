# coding=utf-8
"""
This is Skip Gram form.
"""

import numpy as np
import tensorflow as tf
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import Examples.Dialog.Dialog as Dialog
# Para crear el json
import json
# Para calcular el tiempo
import time
# Para eliminar tildes
import unicodedata
# Para forzar el recolector de basura de Python
import gc

def create_directory_from_fullpath(fullpath):
    """
    Create directory from a fullpath if it not exists.
    """
    directory = os.path.dirname(fullpath)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def write_string_to_pathfile(string, filepath):
    """
    Write a string to a path file
    :param string: string to write
    :param path: path where write
    """
    try:
        create_directory_from_fullpath(filepath)
        file = open(filepath, 'w+')
        file.write(str(string))
    except:
        raise ValueError("No se ha podido escribir el json")

def pt(title=None, text=None):
    """
    Use the print function to print a title and an object coverted to string
    :param title:
    :param text:
    """
    if text is None:
        text = title
        title = "------------------------------------"
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

def delete_accents_marks(string):
    return ''.join((c for c in unicodedata.normalize('NFD', string) if unicodedata.category(c) != 'Mn'))

# function to convert numbers to one hot vectors
def to_one_hot(data_point_index, vocab_size):
    temp = np.zeros(vocab_size)
    temp[data_point_index] = 1
    return temp

def process_for_senteces(sentences):
    """
    Preprocesa las frases para quitarle los singos de acentuación, los puntos, comas, (...)
    """
    processed_sentences = []
    for sentence in sentences:
        sentence_split = sentence.split()
        new_sentence_processed = []
        for word in sentence_split:
            new_sentence_processed.append(delete_accents_marks(word).lower())
        processed_sentences.append(new_sentence_processed)
    #pt("processed_sentences", processed_sentences)
    return processed_sentences


def create_dictionaries(words):
    """
    Crea los diccionarios int2word y word2int a partir de las palabras y las retorna en ese orden
    """
    int2word = {}
    word2int = {}
    for i, word in enumerate(words):
        word2int[word] = i
        int2word[i] = word
    #pt("word2int", word2int)
    #pt("int2word", int2word)
    return word2int, int2word


def get_words_set(processes_sentences):
    """
    A partir de frases preprocesadas, obtiene el conjunto de palabras (sin repetición) de las que se compone
    """
    words = []
    to_delete_marks = [",", ".", ":", ";", "!", "¡", "?", "¿"]
    corpus = [item for sublist in processes_sentences for item in sublist]
    for word in corpus:
        if word not in to_delete_marks:
            words.append(word)
    words = list(set(words))  # Removemos palabras repetidas
    #pt("words",words)
    return words


def generate_training_data(processes_sentences, question_id):
    """
    Genera el conjunto de datos que se utilizará para entrenar a la red una vez estén sean one-hot-vector y a partir de
    la "question_id"
    """
    data = []
    if question_id == "1_x":
        pass
    else:
        WINDOW_SIZE = 5
    for sentence in processes_sentences:
        for word_index, word in enumerate(sentence):
            for nb_word in sentence[max(word_index - WINDOW_SIZE, 0): min(word_index + WINDOW_SIZE, len(sentence)) + 1]:
                if nb_word != word:
                    data.append([word, nb_word])
    #pt("data", data)
    #pt("data", len(data))
    return data

def generate_batches(data, word2int, vocab_size):
    """
    Genera las entradas y los labels a partir de los datos generados previamente.
    """
    x_input = []
    y_label = []
    for data_word in data:
        #pt("dataword", data_word)
        x_input.append(to_one_hot(word2int[data_word[0]], vocab_size))
        y_label.append(to_one_hot(word2int[data_word[1]], vocab_size))
    return np.asarray(x_input), np.asarray(y_label)

def generate_network_and_vector(x_input, y_label, vocab_size, embedding_dim, trains):
    """
    Crea la red neuronal con TensorFlow y utiliza las entradas y los labels para entrenarla. La red consta de 3 capas:
    - Una de entrada
    - Una intermedia
    - Una de salida
    Al hacer Skip Gram, siendo los inputs one-hot-vectors, nos quedamos con los pesos y biases de las dos primeras
    capas. Así, se hace Word Embedding y obtenemos los vectores asociados a las palabras.
    """
    start_time = time.time()
    # making placeholders for x_train and y_train
    x = tf.placeholder(tf.float32, shape=(None, vocab_size))
    y = tf.placeholder(tf.float32, shape=(None, vocab_size))

    EMBEDDING_DIM = embedding_dim  # you can choose your own number # Límite 282 portatil msi 820
    W1 = tf.Variable(tf.random_normal([vocab_size, EMBEDDING_DIM]))
    b1 = tf.Variable(tf.random_normal([EMBEDDING_DIM]))  # bias
    hidden_representation = tf.add(tf.matmul(x, W1), b1)

    W2 = tf.Variable(tf.random_normal([EMBEDDING_DIM, vocab_size]))
    b2 = tf.Variable(tf.random_normal([vocab_size]))
    prediction = tf.nn.softmax(tf.add(tf.matmul(hidden_representation, W2), b2))

    sess = initialize_session()
    # Función de error
    cross_entropy_loss = tf.reduce_mean(-tf.reduce_sum(y_label * tf.log(prediction), reduction_indices=[1]))

    # Optimizador y train_op
    optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.1)
    train_op = optimizer.minimize(cross_entropy_loss)
    n_iters = trains
    optimal_W1 = W1
    optimal_b1 = b1
    min_loss = 1000000000.
    # Entrenamiento
    for _ in range(n_iters):
        #pt(cross_entropy_loss.eval(feed_dict={x: x_input, y: y_label}))
        sess.run(train_op, feed_dict={x: x_input, y: y_label})
        actual_loss = sess.run(cross_entropy_loss, feed_dict={x: x_input, y: y_label})
        #print('Cross Entropy es', sess.run(cross_entropy_loss, feed_dict={x: x_input, y: y_label}))
        if actual_loss < min_loss:
            optimal_W1 = W1
            optimal_b1 = b1
            min_loss = actual_loss
        # Recoger basura
        if _ % 50 == 0:
            gc.collect()
    #pt('Tiempo entrenamiento', str(time.strftime("%Hh%Mm%Ss", time.gmtime((time.time() - start_time)))))
    vectors = sess.run(tf.add(optimal_W1, optimal_b1))
    #pt("vectors", vectors)
    #pt("vectors_shape", vectors.shape)
    return vectors

def euclidean_dist(vec1, vec2):
    return np.sqrt(np.sum((vec1-vec2)**2))

def find_closest(word_index, vectors):
    min_dist = 10000 # to act like positive infinity
    min_index = -1
    query_vector = vectors[word_index]
    for index, vector in enumerate(vectors):
        if euclidean_dist(vector, query_vector) < min_dist and not np.array_equal(vector, query_vector):
            min_dist = euclidean_dist(vector, query_vector)
            min_index = index
    return min_index

def classify_sentence_from_number(number_reference, guidelines):
    """
    A partir de un número de referencia y unas directrices, clasifica el número de referencia dando la "key" de los
    valores de las directrices que sea más cercano al número.
    """
    classification_key = 0
    actual_difference = 999999999.
    for key, number_guideline in guidelines.items():
        if np.abs(number_guideline - number_reference) < actual_difference:
            actual_difference = np.abs(number_guideline - number_reference)
            classification_key = int(key)
    return classification_key

class Word2Vec():
    words_vectors = []
    words = []
    word2int = {}
    int2word = {}
    vocab_size = -1
    question_id = "0"
    name = ""
    total_answers = -1
    accuracy = -1
    # Contiene, por cada pregunta, el número que corresponde al resultado de las operaciones* de los vectores en una
    # frase
    guidelines_results = {}
    json_extension = ".json"
    numpy_extension = ".npy"
    words_vector_str = "-words_vector"

    def to_json(self):
        """
        Convert TFModel class to json with properties method.
        :param attributes_to_delete: String set with all attributes' names to delete from properties method
        :return: sort json from class properties.
        """
        self_dictionary = self.__dict__.copy()
        self_dictionary.pop("words_vectors")
        pt("self_dictionary", self_dictionary)
        json_string =  json.dumps(self, default=lambda o: self_dictionary, sort_keys=True, indent=4)
        return json_string

    def save(self, path, to_txt=False):
        extension = self.numpy_extension
        if to_txt:
            extension = ".out"
        fullpath_json = path + self.name + "-" +  self.question_id + self.json_extension
        fullpath_save = path + self.name + "-" + self.question_id + self.words_vector_str + extension
        try:
            pt("To save", self.to_json())
            write_string_to_pathfile(self.to_json(), fullpath_json)
            if to_txt:
                np.savetxt(fullpath_save, self.words_vectors, delimiter=",")
            else:
                np.save(fullpath_save, self.words_vectors)
            pt("Clase Word2Vec guardada con éxito")
        except:
            raise ValueError("No se ha podido guardar la clase Word2Vec")

    def load(self, path, name, question_id):
        """
        Carga un objeto de clase Word2Vec a partir de un path, un name y una question_id
        """
        try:
            fullpath_numpy = path + name + "-" + question_id + self.words_vector_str + self.numpy_extension
            fullpath_json = path + name + "-" + question_id + self.json_extension
            self.name = name
            self.question_id = question_id
            self.words_vectors = np.load(fullpath_numpy)
            with open(fullpath_json) as json_data:
                word2vec = json.load(json_data)
                self.word2int = word2vec["word2int"]
                self.int2word = word2vec["int2word"]
                self.vocab_size = word2vec["vocab_size"]
                self.guidelines_results = word2vec["guidelines_results"]
                self.words = word2vec["words"]
                self.total_answers = word2vec["total_answers"]
                self.accuracy = word2vec["accuracy"]
            pt("Clase Word2Vec cargada con éxito")
        except:
            raise ValueError("No se ha podido cargar Word2Vec")

    def test_phrases(self, input_sentence=True, sentences_list=None):
        if input_sentence:
            answer = delete_accents_marks(str(input("Escriba su respuesta para la clase:\n")).lower())
            number_reference = sentence_operation(phrase=answer, word2vec_class=self)
            category = classify_sentence_from_number(number_reference=number_reference,
                                                     guidelines=self.guidelines_results)
            pt("Frase", answer)
            pt("Clasificada como", category)
        else:
            for sentence in sentences_list:
                answer = delete_accents_marks(sentence).lower()
                number_reference = sentence_operation(phrase=answer, word2vec_class=self)
                category = classify_sentence_from_number(number_reference=number_reference,
                                                         guidelines=self.guidelines_results)
                pt("Frase", answer)
                pt("Clasificada como", category)

    def test_category(self, questions_dict):
        pt("word2vec_class", self.guidelines_results)
        accuracy, total_answers = test_results(self, questions_dict)
        #insight_to_save(self, save_flag=False)
        pt("accuracy", accuracy)
        pt("total_answers", total_answers)
        pt("word2vec_class.words_vectors.shape", self.words_vectors.shape)

    def __str__(self):
        return ("self.words_vectors" + self.words_vectors + "\n",
                "self.word2int" + self.word2int + "\n",
                "self.int2word" + self.int2word + "\n",
                "self.vocab_size" + self.vocab_size + "\n",
                "self.question_id" + self.question_id + "\n",
                "self.name" + self.name)

    def __repr__(self):
        return ("self.words_vectors" + self.words_vectors + "\n",
                "self.word2int" + self.word2int + "\n",
                "self.int2word" + self.int2word + "\n",
                "self.vocab_size" + self.vocab_size + "\n",
                "self.question_id" + self.question_id + "\n",
                "self.name" + self.name)

def train_phase(name, question_id, dimension_vector, trains, sentences=None):
    #start_time = time.time()
    word2vec_class = Word2Vec()
    processes_sentences = process_for_senteces(sentences)
    word2vec_class.words = get_words_set(processes_sentences)
    word2vec_class.word2int, word2vec_class.int2word = create_dictionaries(word2vec_class.words)
    word2vec_class.vocab_size, word2vec_class.name = len(word2vec_class.words), name
    data = generate_training_data(processes_sentences, question_id)
    x_input, y_label = generate_batches(data, word2vec_class.word2int, word2vec_class.vocab_size)
    vectors = generate_network_and_vector(x_input, y_label, word2vec_class.vocab_size, dimension_vector, trains)
    word2vec_class.words_vectors, word2vec_class.question_id = vectors, question_id
    #pt('Duración total', str(time.strftime("%Hh%Mm%Ss", time.gmtime((time.time() - start_time)))))
    return word2vec_class


def insight_to_save(word2vec_class, save_flag=True, path_to_save_load=None, force_save=False):
    vectors = word2vec_class.words_vectors
    words = word2vec_class.words
    word2int = word2vec_class.word2int
    int2word = word2vec_class.int2word

    from sklearn.manifold import TSNE

    model = TSNE(n_components=2, random_state=0)
    np.set_printoptions(suppress=True)
    vectors = model.fit_transform(vectors)

    from sklearn import preprocessing

    normalizer = preprocessing.Normalizer()
    vectors = normalizer.fit_transform(vectors, '85')

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    #pt("words", words)
    for word in words:
        #pt("Más cercano a " + word, int2word[find_closest(word2int[word], vectors)])
        ax.annotate(word, (vectors[word2int[word]][0], vectors[word2int[word]][1]))

    axes = plt.gca()
    axes.set_xlim([-2, +2])
    axes.set_ylim([-2, +2])
    # No mostrar gráfica = línea siguiente comentada
    #plt.show()

    if force_save:
        pt("Se guarda clase-->" + word2vec_class.name + " y question_id-->" + word2vec_class.question_id + "\n")
        word2vec_class.save(path=path_to_save_load)
        pt("Generado y guardado con éxito")
    elif save_flag:
        pt("Se guardaría clase-->" + word2vec_class.name + " y question_id-->" + word2vec_class.question_id + "\n")
        save = str(input("Para guardar vector escribir la letra \"s\"")).lower()
        if save == "s":
            word2vec_class.save(path=path_to_save_load)
            pt("Generado y guardado con éxito")
        else:
            pt("No guardado")


def phrase_processed(list_of_words):
    words = []
    for word in list_of_words:
        split = word.split()
        for word in split:
            alpha_word = ''.join([i for i in word if (i.isalpha() or i.isdigit())])
            if alpha_word != "" and alpha_word != " ":
                words.append(alpha_word)
    return words

def process_answer(answer, word2vec_class):
    """
    A partir de una respuesta, la convierte en un vector y, después, lo transforma en un número entero.
    """
    words_vector = []
    words_to_return = []
    pt("answer", answer)
    words = phrase_processed(answer.split(sep=" "))
    pt("words", words)
    for word in words:
        if word in word2vec_class.word2int.keys():
            word_index =  word2vec_class.word2int[word]
            word_vector = word2vec_class.words_vectors[word_index]
            pt("word: " + word + " índice", word_index)
            pt("word: " + word + " vector", word_vector)
            words_vector.append(word_vector)
            words_to_return.append(word)
        else:
            # word_vector = np.zeros(50,dtype=np.float32)
            # No hacemos nada
            pass
    pt("words_vector", words_vector)
    return words_vector, words_to_return

def process_vector(answer2vector, words, word2vec_class):
    total_words = float(len(words))
    squared_vectors = []
    for vector in answer2vector:
        squared_vector = vector**2
        squared_vectors.append(squared_vector)
    sum_squared_vectors = np.sum(squared_vectors) / total_words
    pt("sum_squared_vectors", sum_squared_vectors)
    return sum_squared_vectors

def test_results(word2vec_class, question_dict):
    """
    Realizamos las preguntas y contestamos, convirtiendo las respuestas en números a través de los vectores
    """
    total_accuracies = 0
    total_answers = 0
    for question, answers in question_dict.items():
        guidelines = word2vec_class.guidelines_results
        for answer in answers:
            number_result = sentence_operation(answer, word2vec_class)
            question_id = classify_sentence_from_number(number_reference=number_result, guidelines=guidelines)
            """
            actual_difference = 10000000.
            question_id = -1
            for question_id_reference, reference_number in guidelines.items():
                absolute_difference = np.abs(number_result - reference_number)
                if absolute_difference < actual_difference:
                    question_id = question_id_reference
                    actual_difference = absolute_difference
            """
            if int(question_id) == int(question):
                total_accuracies += 1
            total_answers += 1
    return total_accuracies, total_answers

def test_individual_sentence(word2vec_class, answer):
    """
    A partir de una respuesta, se obtiene el resultado de las operaciones y se compara con las directrices para
    clasificarla.
    """
    answer2vector, words = process_answer(answer, word2vec_class)
    result = process_vector(answer2vector, words, word2vec_class)

def operation_final(operational_list):
    """
    Realizamos las operaciones para retornar un número que representará a una pregunta de una categoría.
    """
    return int(np.mean(operational_list))

def sentence_operation(phrase, word2vec_class):
    """
    A partir de una frase, obtiene el vector de cada palabra y retorna un número resultado de la operación a partir
    de esos vectores.
    """
    list_of_words = phrase.split(sep=" ")
    words = phrase_processed(list_of_words=list_of_words)
    results_list = []
    for word in words:
        if word in word2vec_class.words:
            # Obtenemos el índice de la palabra
            word_index = word2vec_class.word2int[word]
            # Obtenemos vector de la palabra a partir del índice
            word_vector = word2vec_class.words_vectors[word_index]
            operation = np.mean((word_vector*28)**4)
            pt("word", word)
            pt("word_index", word_index)
            pt("operation --> np.mean((word_vector*28)**4)", operation)
            pt("word_vector", word_vector)
            results_list.append(operation)
    return np.mean(results_list)

def generate_guidelines(word2vec_class, questions_dict):
    """
    A partir del diccionario de palabras, crea las directrices para la clase word2vec
    """
    guidelines = {}
    #pt("keys", questions_dict.keys())
    for key in questions_dict.keys():
        operational_list = []
        for phrase in questions_dict[key]:
            operational_list.append(sentence_operation(phrase, word2vec_class))
        key_number_representation = operation_final(operational_list)
        guidelines[key] = key_number_representation
    return guidelines

def generate_word2vec_chatbot(category, question_id, highlighted_words, question_dict, repetitions=10, train=True,
                              force_save=False):
    if train:
        path_to_save_load = "..\\Dialog\\Corpus\\"
        final_accuracy = 0
        accuracies = []
        total_answers = None
        word2vec_class_to_save = None
        start_time = time.time()
        for _ in range(repetitions):
            # Generar vectores
            word2vec_class = train_phase(name=category.name, question_id=question_id,
                                         dimension_vector=50, trains=500, sentences=highlighted_words)
            word2vec_class.guidelines_results = generate_guidelines(word2vec_class, question_dict)
            # pt("word2vec_class.guidelines_results", word2vec_class.guidelines_results)
            accuracy, total_answers = test_results(word2vec_class, question_dict)
            accuracies.append(accuracy)
            pt("accuracies", accuracies)
            if accuracy > final_accuracy:
                final_accuracy = accuracy
                word2vec_class.accuracy = final_accuracy
                word2vec_class.total_answers = total_answers
                word2vec_class_to_save = word2vec_class
                pt("total_answers", total_answers)
                pt("max_accuracy", accuracy)
            gc.collect()
            pt('Tiempo actual para ' + category.name + question_id,
               str(time.strftime("%Hh%Mm%Ss", time.gmtime((time.time() - start_time)))))
        pt("total_answers", total_answers)
        pt('Duración total', str(time.strftime("%Hh%Mm%Ss", time.gmtime((time.time() - start_time)))))
        insight_to_save(word2vec_class_to_save, save_flag=True, path_to_save_load=path_to_save_load,
                        force_save=force_save)

def load_guidelines_chatbot(category, question_id):
    path_to_save_load = "..\\Dialog\\Corpus\\"
    word2vec_class = Word2Vec()
    # Para cargar
    word2vec_class.load(path=path_to_save_load, name=category.name,
                                     question_id=question_id)
    return word2vec_class


def execution(repetitions, train, force_save):
    """
    Se recorren los bloques de preguntas para formar los json y los vectores de cada uno de ellos.
    """
    for topic in Dialog.topics:
        scheme = topic[1]
        name_scheme = scheme.name
        pt("scheme", name_scheme)
        # ESTRÉS
        if name_scheme == "Stress":
            # Solo existe un tipo de respuestas: {0:no_se, 1:nunca, 2:algunas_veces, 3:bastantes_veces, 4: siempre}
            question_id = scheme.id_pregunta_1
            highlighted_words = scheme.palabras_destacadas_pregunta_1
            question_dict = scheme.answers_dict
            generate_word2vec_chatbot(category=scheme, question_id=question_id, highlighted_words=highlighted_words,
                                      question_dict=question_dict, repetitions=repetitions, train=train,
                                      force_save=force_save)
            word2vec = load_guidelines_chatbot(category=scheme, question_id=question_id)
            #word2vec.save(path="..\\Dialog\\Corpus\\", to_txt=True)
            #word2vec.test_category(questions_dict=question_dict)
            #word2vec.test_phrases(input_sentence=False, sentences_list=["si"])
            # Para testear
            pt("scheme", name_scheme)
            pt("{0:no_se, 1:nunca, 2:algunas_veces, 3:bastantes_veces, 4: siempre} -->0", question_id)
            word2vec.test_phrases()
        # FUMAR
        elif name_scheme == "Smoke":
            # Dos tipos de respuestas:
            # {0:no_se, 1:no, 2:si}
            # {0:no_se, 1:<10, 2:10-15, 3:>15}
            for i in range(2):
                if i == 0:
                    question_id = scheme.id_pregunta_1
                    highlighted_words = scheme.palabras_destacadas_pregunta_1
                    question_dict = scheme.answer_dict_question_1
                else:
                    question_id = scheme.id_pregunta_2
                    highlighted_words = scheme.palabras_destacadas_pregunta_2
                    question_dict = scheme.answer_dict_question_2
                generate_word2vec_chatbot(category=scheme, question_id=question_id, highlighted_words=highlighted_words,
                                          question_dict=question_dict, repetitions=repetitions, train=train,
                                          force_save=force_save)
                word2vec = load_guidelines_chatbot(category=scheme, question_id=question_id)
                #word2vec.save(path="..\\Dialog\\Corpus\\", to_txt=True)
                #word2vec.test_category(questions_dict=question_dict)
                #word2vec.test_phrases(input_sentence=False, sentences_list=["si"])
                # Para testear
                pt("scheme", name_scheme)
                pt("no o si --> 0, {0:no_se, 1:<10, 2:10-15, 3:>15} -->1", question_id)
                word2vec.test_phrases()
        # DIETA
        elif name_scheme == "Diet":
            # Un tipo de respuesta:
            # {0: no_se, 1:<1, 2:1-2, 3:3-5, 4:>5}
            question_id = scheme.id_pregunta_1
            highlighted_words = scheme.palabras_destacadas_pregunta_1
            question_dict = scheme.answer_dict_question_1
            generate_word2vec_chatbot(category=scheme, question_id=question_id, highlighted_words=highlighted_words,
                                      question_dict=question_dict, repetitions=repetitions, train=train,
                                      force_save=force_save)
            word2vec = load_guidelines_chatbot(category=scheme, question_id=question_id)
            #word2vec.save(path="..\\Dialog\\Corpus\\", to_txt=True)
            #word2vec.test_category(questions_dict=question_dict)
            #word2vec.test_phrases(input_sentence=False, sentences_list=["1"])
            # Para testear
            pt("scheme", name_scheme)
            word2vec.test_phrases()
        # ACTIVIDAD
        elif name_scheme == "Activity":
            # Dos tipos de respuestas:
            # {0:no_se, 1:no, 2:si}
            # {0:no_se, 1:0-1, 2:2-3, 3:4-6 4:>6}
            for i in range(2):
                if i == 0:
                    question_id = scheme.id_pregunta_1
                    highlighted_words = scheme.palabras_destacadas_pregunta_1
                    question_dict = scheme.answer_dict_question_1
                else:
                    question_id = scheme.id_pregunta_2
                    highlighted_words = scheme.palabras_destacadas_pregunta_2
                    question_dict = scheme.answer_dict_question_2
                generate_word2vec_chatbot(category=scheme, question_id=question_id, highlighted_words=highlighted_words,
                                          question_dict=question_dict, repetitions=repetitions, train=train,
                                          force_save=force_save)
                word2vec = load_guidelines_chatbot(category=scheme, question_id=question_id)
                #word2vec.save(path="..\\Dialog\\Corpus\\", to_txt=True)
                #word2vec.test_category(questions_dict=question_dict)
                #word2vec.test_phrases(input_sentence=False, sentences_list=["si"])
                # Para testear
                pt("scheme", name_scheme)
                pt("no o si --> 0, {0:no_se, 1:0-1, 2:2-3, 3:4-6 4:>6} -->1", question_id)
                word2vec.test_phrases()

        # SUEÑO
        elif name_scheme == "Sleep":
            # Dos tipos de respuestas:
            # {0:no_se, 1:<5, 2:5-8, 3:>8}
            # {0:no_se, 1:nunca, 2:algunas_veces, 3:bastantes_veces, 4: siempre}
            for i in range(2):
                if i == 0:
                    question_id = scheme.id_pregunta_1
                    highlighted_words = scheme.palabras_destacadas_pregunta_1
                    question_dict = scheme.answer_dict_question_1
                else:
                    question_id = scheme.id_pregunta_2
                    highlighted_words = scheme.palabras_destacadas_pregunta_2
                    question_dict = scheme.answer_dict_question_2
                generate_word2vec_chatbot(category=scheme, question_id=question_id, highlighted_words=highlighted_words,
                                          question_dict=question_dict, repetitions=repetitions, train=train,
                                          force_save=force_save)
                word2vec = load_guidelines_chatbot(category=scheme, question_id=question_id)
                #word2vec.save(path="..\\Dialog\\Corpus\\", to_txt=True)
                #word2vec.test_category(questions_dict=question_dict)
                #word2vec.test_phrases(input_sentence=False, sentences_list=["si"])
                # Para testear
                pt("scheme", name_scheme)
                pt("{0:no_se, 1:<5, 2:5-8, 3:>8} --> 0,"
                   " {0:no_se, 1:nunca, 2:algunas_veces, 3:bastantes_veces, 4: siempre} -->1", question_id)
                word2vec.test_phrases()
        else:
            pass



if __name__ == '__main__':
    # Tener cuidado con la memoria
    # Modo recolector de basura activado. Para desactivarlo, eliminar código donde líneas sea = a "gc.collect()"
    execution(repetitions=50, train=False, force_save=False)