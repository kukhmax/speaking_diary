import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import Home from '../screens/Home';
import Record from '../screens/Record';
import Review from '../screens/Review';
import Settings from '../screens/Settings';

export type RootStackParamList = {
  Home: undefined;
  Record: undefined;
  Review: { entryId?: string } | undefined;
  Settings: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export const RootNavigator = () => (
  <Stack.Navigator>
    <Stack.Screen name="Home" component={Home} />
    <Stack.Screen name="Record" component={Record} />
    <Stack.Screen name="Review" component={Review} />
    <Stack.Screen name="Settings" component={Settings} />
  </Stack.Navigator>
);