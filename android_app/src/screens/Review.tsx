import React, { useEffect, useState } from 'react';
import { View, Text, ActivityIndicator, ScrollView } from 'react-native';
import { useTranslation } from 'react-i18next';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation';
import { postReview } from '../api/review';
import Constants from 'expo-constants';

type Props = NativeStackScreenProps<RootStackParamList, 'Review'>;

export default function Review({ route }: Props) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [corrected, setCorrected] = useState('');
  const [explanations, setExplanations] = useState<string[]>([]);
  const text = route.params?.text || '';
  const extra = (Constants.expoConfig?.extra || {}) as { uiLanguage?: string };
  const uiLang = extra.uiLanguage || 'pl';

  useEffect(() => {
    const run = async () => {
      if (!text) return;
      setLoading(true);
      try {
        const res = await postReview({ text, ui_language: uiLang });
        setCorrected(res?.corrected_html || '');
        // пока используем explanations_html как plain text
        const lines = (res?.explanations_html || '').split('<br>').filter(Boolean);
        setExplanations(lines);
      } catch (e) {
        console.log('Review error', e);
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [text, uiLang]);

  return (
    <ScrollView contentContainerStyle={{ flexGrow: 1, alignItems: 'center', justifyContent: 'center', padding: 16 }}>
      <Text style={{ fontSize: 18, marginBottom: 12 }}>{t('review.title', 'Review')}</Text>
      {loading ? (
        <ActivityIndicator />
      ) : (
        <View style={{ width: '100%' }}>
          <Text style={{ marginBottom: 8 }}>{t('review.placeholder', 'Corrections and explanations will appear here.')}</Text>
          <Text style={{ fontWeight: 'bold', marginBottom: 8 }}>Corrected:</Text>
          <Text style={{ marginBottom: 12 }}>{corrected}</Text>
          {explanations.length > 0 && (
            <View>
              <Text style={{ fontWeight: 'bold', marginBottom: 8 }}>Explanations:</Text>
              {explanations.map((line, idx) => (
                <Text key={idx} style={{ marginBottom: 4 }}>• {line}</Text>
              ))}
            </View>
          )}
        </View>
      )}
    </ScrollView>
  );
}