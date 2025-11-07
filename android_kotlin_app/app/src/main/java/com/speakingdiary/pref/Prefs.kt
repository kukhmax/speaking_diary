package com.speakingdiary.pref

import android.content.Context
import android.content.SharedPreferences

object Prefs {
    private const val FILE = "speaking_diary_prefs"
    private const val KEY_BASE_URL = "base_url"
    private const val KEY_TOKEN = "access_token"
    private const val KEY_UI_LANG = "ui_language"

    private fun sp(ctx: Context): SharedPreferences =
        ctx.getSharedPreferences(FILE, Context.MODE_PRIVATE)

    fun getBaseUrl(ctx: Context): String? = sp(ctx).getString(KEY_BASE_URL, null)
    fun setBaseUrl(ctx: Context, value: String?) { sp(ctx).edit().putString(KEY_BASE_URL, value).apply() }

    fun getToken(ctx: Context): String? = sp(ctx).getString(KEY_TOKEN, null)
    fun setToken(ctx: Context, value: String?) { sp(ctx).edit().putString(KEY_TOKEN, value).apply() }

    fun getUiLanguage(ctx: Context): String = sp(ctx).getString(KEY_UI_LANG, "ru") ?: "ru"
    fun setUiLanguage(ctx: Context, value: String) { sp(ctx).edit().putString(KEY_UI_LANG, value).apply() }
}