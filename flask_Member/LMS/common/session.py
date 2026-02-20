import pymysql

class Session:

    @staticmethod
    def get_connection():   # 데이터 베이스에 연결
        print("get_connection()메서드 호출 - mysql에 접속됩니다.")

        return pymysql.connect(
            host='192.168.0.154',
            user='LHJ',
            password='1021',
            db='lhj_mbc',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

