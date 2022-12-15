/*Gets top three songs in last 7 days*/
select name, artist_name, album_name, COUNT(name) AS count  
    FROM history 
    WHERE played_at > CURRENT_DATE - 7 
    GROUP BY name, artist_name, album_name 
    ORDER BY count 
    DESC 
    LIMIT 3;
