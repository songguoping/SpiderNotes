# -*- coding: utf-8 -*-
# @Time    : 5/9/17 10:11
__author__ = 'guoping'
import requests
import MySQLdb
from scrapy.selector import Selector

conn = MySQLdb.connect(host="127.0.0.1", user="root", passwd="root", db="article_spider", charset="utf8")
cursor = conn.cursor()


def crawl_ips():
    # 爬取西刺的免费ip代理
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0"}
    for i in range(15):
        re = requests.get("http://www.httpsdaili.com/?page={0}".format(i), headers=headers)
        selector = Selector(text=re.text)
        all_trs = selector.css('.table-bordered.table-striped tbody tr')

        ip_list = []
        for tr in all_trs[1:]:
            all_texts = tr.css("td::text").extract()

            ip = all_texts[0]
            port = all_texts[1]
            proxy_type = all_texts[3]

            ip_list.append((ip, port, proxy_type))

        for ip_info in ip_list:
            cursor.execute(
                "insert proxy_ip(ip, port,  proxy_type) VALUES('{0}', '{1}',  'HTTP') ON DUPLICATE KEY UPDATE ip=VALUES(ip), port=VALUES(port)".format(
                    ip_info[0], ip_info[1]
                )
            )

            conn.commit()


class GetIP(object):
    def delete_ip(self, ip):
        # 从数据库中删除无效的ip
        delete_sql = """
            delete from proxy_ip where ip='{0}'
        """.format(ip)
        cursor.execute(delete_sql)
        conn.commit()
        return True

    def judge_ip(self, ip, port):
        # 判断ip是否可用
        http_url = "http://www.baidu.com"
        proxy_url = "http://{0}:{1}".format(ip, port)
        try:
            proxy_dict = {
                "http": proxy_url,
            }
            response = requests.get(http_url, proxies=proxy_dict)
        except Exception as e:
            print("invalid ip and port")
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code >= 200 and code < 300:
                print("effective ip")
                return True
            else:
                print("invalid ip and port")
                self.delete_ip(ip)
                return False

    def get_random_ip(self):
        # 从数据库中随机获取一个可用的ip
        random_sql = """
                      SELECT ip, port FROM proxy_ip
                    ORDER BY RAND()
                    LIMIT 1
                    """
        result = cursor.execute(random_sql)
        for ip_info in cursor.fetchall():
            ip = ip_info[0]
            port = ip_info[1]

            judge_re = self.judge_ip(ip, port)
            if judge_re:
                return "http://{0}:{1}".format(ip, port)
            else:
                return self.get_random_ip()


# print(crawl_ips())
# if __name__ == "__main__":
#
#     get_ip = GetIP()
#     get_ip.get_random_ip()
