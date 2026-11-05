"""Rebuild the four November 5 afternoon articles using the site's daily template."""
from build_blog_20261105 import main as assemble, BACKLINKS

if __name__ == "__main__":
    BACKLINKS.clear()
    BACKLINKS.update({
        "pond": ("水路", "共同で支える水の行き先を家族に伝えるときは、池の名前に地区名も添えると場所を確かめられます。"),
        "oak": ("森林", "持ち山を引き継ぐ際には、秋に色が変わった木の位置を記録しておく方法もあります。"),
        "storage": ("茶", "家庭で風味を保つには、暖房を入れる前に茶葉を置く棚も確かめておきたいところです。"),
        "solar": ("農地", "事業用の太陽光設備を置く提案なら、計画の敷地面積と撤去の段取りも別に確かめられます。"),
    })
    assemble()
