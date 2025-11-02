import React from 'react';
import { View, Text } from 'react-native';
import { useTranslation } from 'react-i18next';

export default function Settings() {
  const { t } = useTranslation();
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <Text style={{ fontSize: 18 }}>{t('settings.title', 'Settings')}</Text>
      <Text>{t('settings.language', 'Interface language')}</Text>
    </View>
  );
}