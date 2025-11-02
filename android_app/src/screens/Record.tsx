import React, { useRef, useState } from 'react';
import { View, Text, Button } from 'react-native';
import { Audio } from 'expo-av';
import { useTranslation } from 'react-i18next';

export default function Record() {
  const { t } = useTranslation();
  const recordingRef = useRef<Audio.Recording | null>(null);
  const [isRecording, setIsRecording] = useState(false);

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
    // TODO: upload to /api/transcribe with UI language
    console.log('Recorded file:', uri);
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