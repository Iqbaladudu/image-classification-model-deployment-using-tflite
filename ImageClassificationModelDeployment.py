# -*- coding: utf-8 -*-
"""ImageClssificationModelDeployment.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1F0DsxupRsPDDytyynJAYnwKbIsa-tfo_
"""

# Install Kaggle
! pip install kaggle

# Mount ke Google Drive
from google.colab import drive
drive.mount('/content/gdrive')

# Setup folder
import os
os.environ['KAGGLE_CONFIG_DIR'] = "/content/gdrive/My Drive/Kaggle"

!kaggle datasets download -d mahmoudreda55/satellite-image-classification

os.mkdir("satelliteimage")

import shutil

# Unzip dataset
shutil.unpack_archive("satellite-image-classification.zip", "/content/satelliteimage")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

dir = "/content/satelliteimage/data"

from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Preprocessing
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    horizontal_flip=True,
    shear_range=0.2,
    fill_mode='nearest',
    validation_split=0.20
)

test_datagen = ImageDataGenerator(rescale=1./255, validation_split=0.20)

train_generator = train_datagen.flow_from_directory(
    dir,
    target_size=(150, 150),
    batch_size=4,
    class_mode="categorical", # default
    subset="training"
)

validation_generator = test_datagen.flow_from_directory(
    dir,
    target_size=(150, 150),
    batch_size=4,
    class_mode="categorical", # default
    subset="validation"
)

classes = len(os.listdir(dir))
classes

from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications import ResNet152V2
from tensorflow.keras.layers import Input
import tensorflow as tf

model = tf.keras.models.Sequential([
    tf.keras.Input(shape=(150, 150, 3)),
    ResNet152V2(weights="imagenet", include_top=False, input_tensor=Input(shape=(150, 150, 3))),
    tf.keras.layers.Conv2D(16, (3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2, 2),
    tf.keras.layers.Dense(512, activation="relu"),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(512, activation="relu"),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(512, activation="relu"),
    tf.keras.layers.Dense(512, activation="relu"),
    tf.keras.layers.Dense(512, activation="relu"),
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(classes, activation='softmax')
])

model.layers[0].trainable = False

model.summary()

# compile model dengan 'adam' optimizer loss function 'categorical_crossentropy' 
model.compile(loss='categorical_crossentropy',
              optimizer=tf.optimizers.Adam(),
              metrics=['accuracy'])

class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if logs.get('accuracy')>0.92 and logs.get('val_accuracy') >0.92:
      print("\nAkurasi telah mencapai >92%!")
      self.model.stop_training = True
callbacks = myCallback()

# latih model dengan model.fit 
history = model.fit(
      train_generator,
      steps_per_epoch=100,
      epochs=30,
      validation_data=validation_generator,
      validation_steps=5,
      callbacks=[callbacks],
      verbose=2)

# Evaluasi Hasil

# Accuracy dan validation
acc = history.history['accuracy']
val_acc = history.history['val_accuracy']

# Loss dan validation
loss = history.history['loss']
val_loss = history.history['val_loss']

epochs = range(len(acc))

# Accuracy & validation plot
plt.plot(epochs, acc, label="accuracy")
plt.plot(epochs, val_acc, label="validation accuracy")
plt.title('Akurasi Training dan Validation')
plt.legend(loc="upper left")

# Loss & validation plot
plt.plot(epochs, loss, label="loss")
plt.plot(epochs, val_loss, label="validation loss")
plt.legend(loc="upper left")
plt.title('Loss training dan validation')

import pathlib

# Menyimpan model dalam format SavedModel
export_dir = 'saved_model/'
tf.saved_model.save(model, export_dir)

# Convert SavedModel menjadi satelliteimageclassification.tflite
converter = tf.lite.TFLiteConverter.from_saved_model(export_dir)
tflite_model = converter.convert()

tflite_model_file = pathlib.Path('satelliteimage.tflite')
tflite_model_file.write_bytes(tflite_model)