package com.speakingdiary.data.local

import androidx.room.*
import com.speakingdiary.data.model.Entry
import kotlinx.coroutines.flow.Flow

@Dao
interface EntryDao {
    @Query("SELECT * FROM entries ORDER BY createdAt DESC")
    fun getAllEntries(): Flow<List<Entry>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEntry(entry: Entry)

    @Query("SELECT * FROM entries WHERE id = :id")
    suspend fun getEntryById(id: Int): Entry?
    
    @Query("DELETE FROM entries WHERE id = :id")
    suspend fun deleteEntry(id: Int)
}