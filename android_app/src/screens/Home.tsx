import React from 'react';
import { View, Text, Button } from 'react-native';
import { useTranslation } from 'react-i18next';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation';

type Props = NativeStackScreenProps<RootStackParamList, 'Home'>;

export default function Home({ navigation }: Props) {
  const { t } = useTranslation();
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <Text style={{ fontSize: 20 }}>{t('home.title', 'Voice Diary')}</Text>
      <Button title={t('home.record', 'Record')} onPress={() => navigation.navigate('Record')} />
      <Button title={t('home.review', 'Review')} onPress={() => navigation.navigate('Review')} />
      <Button title={t('home.settings', 'Settings')} onPress={() => navigation.navigate('Settings')} />
    </View>
  );
}