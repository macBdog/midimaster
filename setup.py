from setuptools import setup

setup(name='midimaster',
      version='0.1',
      description='A rhythm game that uses MIDI files and input and musical notation.',
      url='http://github.com/macbdog/midimaster',
      author='Charles Henden',
      author_email='charles@henden.com.au',
      license='MIT',
      packages=['midimaster'],
      install_requires=[
          'glfw',
          'pillow',
          'numpy',
          'mido',
          'python-rtmidi',
          'PyOpenGL',
          'PyOpenGL-accelerate',
          'freetype-py',
      ],
      zip_safe=True)
