
# LMS/service/BoardService.py

from LMS.common import Session


class BoardService:

    @staticmethod
    def list(board_type="notice", keyword=""):
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:

                sql = """
                    SELECT
                      b.id,
                      b.title,
                      b.board_type,
                      b.is_pinned,
                      b.display_date,
                      b.created_at,
                      b.view_count,

                      m.name AS writer_name,
                      m.uid  AS writer_uid,

                      (SELECT COUNT(*) FROM board_likes bl WHERE bl.board_id = b.id) AS like_count,
                      (SELECT COUNT(*) FROM board_comments bc WHERE bc.board_id = b.id) AS comment_count

                    FROM boards b
                    JOIN members m ON b.member_id = m.id
                    WHERE b.board_type = %s
                """

                params = [board_type]

                if keyword:
                    sql += " AND (b.title LIKE %s OR b.content LIKE %s) "
                    like = f"%{keyword}%"
                    params.extend([like, like])

                sql += """
                    ORDER BY
                      b.is_pinned DESC,
                      COALESCE(b.display_date, DATE(b.created_at)) DESC,
                      b.id DESC
                """

                cursor.execute(sql, params)
                return cursor.fetchall()

        finally:
            conn.close()