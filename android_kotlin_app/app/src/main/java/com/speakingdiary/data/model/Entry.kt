package com.speakingdiary.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.util.Date

@Entity(tableName = "entries")
data class Entry(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,
    val text: String,
    val language: String,
    val duration: Double = 0.0,
    val createdAt: Long = Date().time,
    val date: String = Date().toString().split(" ").take(3).joinToString(" ")
)