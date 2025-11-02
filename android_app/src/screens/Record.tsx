import React, { useRef, useState } from 'react';
import { View, Text, Button } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation';
import { Audio } from 'expo-av';
import { useTranslation } from 'react-i18next';
import { transcribeAudio } from '../api/transcribe';

export default function Record() {
  const { t } = useTranslation();
  const recordingRef = useRef<Audio.Recording | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();

  const startRecording = async () => {
    const { granted } = await Audio.requestPermissionsAsync();
    if (!granted) return;
    await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
    const recording = new Audio.Recording();
    await recording.prepareToRecordAsync(Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY);
    await recording.startAsync();
    recordingRef.current = recording;
    setIsRecording(true);
  };

  const stopRecording = async () => {
    const recording = recordingRef.current;
    if (!recording) return;
    await recording.stopAndUnloadAsync();
    const uri = recording.getURI();
    setIsRecording(false);
    if (!uri) return;
    try {
      const res = await transcribeAudio(uri, 'auto');
      const text = res?.text || '';
      navigation.navigate('Review', { text });
    } catch (e) {
      console.log('Transcribe error', e);
    }
  };

  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <Text style={{ fontSize: 18 }}>{t('record.title', 'Record your voice')}</Text>
      {!isRecording ? (
        <Button title={t('record.start', 'Start Recording')} onPress={startRecording} />
      ) : (
        <Button title={t('record.stop', 'Stop Recording')} onPress={stopRecording} />
      )}
    </View>
  );
}