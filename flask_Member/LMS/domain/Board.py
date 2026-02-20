
class Board:

    def __init__(self, id=None,
                 member_id=None,
                 title="",
                 content="",
                 created_at=None,
                 view_count=0,
                 board_type="notice",
                 is_pinned=0,
                 display_date=None,
                 writer_name=None,
                 writer_uid=None):

        self.id = id
        self.member_id = member_id
        self.title = title
        self.content = content
        self.created_at = created_at
        self.view_count = view_count
        self.board_type = board_type
        # notice/free/qna 탭 구분
        self.is_pinned = is_pinned
        # 상단고정 여부(0/1)
        self.display_date = display_date
        # 화면에 보여줄 작성일(선택 입력)
        self.writer_name = writer_name
        # 작성자 이름(JOIN으로 가져올 값)
        self.writer_uid = writer_uid
        # 작성자 아이디(JOIN으로 가져올 값)

    @staticmethod
    def from_db(row):
        if not row:
            return None
        return Board(
            id=row.get("id"),
            member_id=row.get("member_id"),
            title=row.get("title"),
            content=row.get("content"),
            created_at=row.get("created_at"),
            view_count=row.get("view_count", 0),
            board_type=row.get("board_type", "notice"),
            is_pinned=row.get("is_pinned", 0),
            display_date=row.get("display_date"),
            writer_name=row.get("writer_name"),
            writer_uid=row.get("writer_uid"),
        )
        # dict → 객체 변환해서 반환