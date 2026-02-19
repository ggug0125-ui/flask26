class Member:

    def __init__(self, id, uid, password, name, role="user", active=True):  # 객체 가져오기
        self.id = id
        self.uid = uid
        self.password = password
        self.name = name
        self.role = role
        self.active = active

    @classmethod
    def from_db(cls, row: dict):
        """
        DictCursor로부터 전달받은 딕셔너리 데이터를 Member 객체로 변환합니다.
        """
        if not row:
            return None

        member = cls(
            id=row.get('id'),
            uid=row.get('uid'),
            password=row.get('password'),
            name=row.get('name'),
            role=row.get('role'),
            active=bool(row.get('active'))
        )

        member.created_at = row.get('created_at')

        return member

    def is_admin(self):
        return self.role == "admin"

    def __str__(self):
        return f"{self.name}({self.uid}) [{self.role}]"