/* Returns top three artists in the past week.*/
select artist_name, count(artist_name) as count 
    FROM history 
    WHERE played_at > CURRENT_DATE - 7 
    GROUP BY artist_name 
    ORDER BY count 
    DESC 
    LIMIT 3;