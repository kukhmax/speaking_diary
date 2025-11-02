import React from 'react';
import { View, Text } from 'react-native';
import { useTranslation } from 'react-i18next';

export default function Review() {
  const { t } = useTranslation();
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <Text style={{ fontSize: 18 }}>{t('review.title', 'Review')}</Text>
      <Text>{t('review.placeholder', 'Corrections and explanations will appear here.')}</Text>
    </View>
  );
}