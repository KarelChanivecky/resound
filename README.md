# Resound - A musical instrument tuner

By: Karel Chanivecky Garcia

## VERSION:
- 0.6: Musical notes are now identified in reference to note
- 0.5: Recorder, Frequency identification, basic program entry point implemented

## LEARNING GOALS:
- Apply threading synchronization to a useful, practical problem using a consumer/producer pattern
- Explore numpy and scipy functionality
- Gain better understanding of signal windowing and Discrete Fourier Transforms
- Apply knowledge obtained in statistics course
- Deepen understanding of programing in python through the use of procedural and OO paradigms
- Learn UI implementation with Python
- Learn how to use record and play sound with python

## CURRENT STATE:
- Threading synchronization pattern is implemented
- Recording is implemented. sound_device library was selected to record sound from microphone
- Frequency identification is implemented
- Integration test between recording and frequency identification modules
- Frequency identification module is unit tested
- Musical note identification based on frequency identified
- Musical note identification unit tested
- Musical note identification integration tested

## SOON TO COME:
- Tuner UI
- Optimization of frequency identification accuracy
- Refactor consumer/producer classes to reduce code duplication and boilerplating

## KNOWN LIMITATIONS:
- It is not accurate enough to use professionally; empirical optimization of parameters ensues to achieve desired results

## BIBLIOGRAPHY:

- Improving FFT resolution. J. Marsar. 2015<br>
  http://www.add.ece.ufl.edu/4511/references/ImprovingFFTResoltuion.pdf
- Improving FFT frequency measurement resolution by parabolic and gaussian interpolation. M. Gasior, J.L. Gonzalez. 2004.<br>
  https://mgasior.web.cern.ch/pap/FFT_resol_note.pdf
- Physics of Music - Notes. MTU. Accessed Mar 20, 2021.<br>
  https://pages.mtu.edu/~suits/notefreqs.html
  https://pages.mtu.edu/~suits/NoteFreqCalcs.html