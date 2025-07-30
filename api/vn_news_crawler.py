import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading


class NewsCrawler:
    """Base class for news crawlers"""
    def __init__(self):
        self.base_url = ""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.categories = {}
        self.category_names = {}
        self.source_name = "Unknown"
        
    def get_page_content(self, url):
        """Tải nội dung trang web từ URL"""
        try:
            print(f"Đang tải URL: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Hiển thị kích thước nội dung
            content_length = len(response.text)
            print(f"Đã tải thành công, kích thước: {content_length} bytes")
            
            return response.text
        except requests.RequestException as e:
            print(f"Lỗi khi tải trang {url}: {e}")
            return None
            
    def parse_article_list(self, html_content, category_id):
        """Phân tích danh sách bài viết từ trang danh mục"""
        raise NotImplementedError("Subclasses must implement this method")
        
    def parse_article_detail(self, url, category_id):
        """Phân tích chi tiết bài viết từ URL"""
        raise NotImplementedError("Subclasses must implement this method")
        
    def crawl_category(self, category, num_pages=2, callback=None):
        """Crawl dữ liệu từ một danh mục cụ thể"""
        articles = []
        category_id = self.categories.get(category)

        for page in range(1, num_pages + 1):
            url = self.get_category_url(category, page)

            message = f"Đang crawl trang {page} của danh mục {self.category_names.get(category_id, category)}..."
            print(message)
            if callback:
                callback(message)

            html_content = self.get_page_content(url)

            page_articles = self.parse_article_list(html_content, category_id)
            if not page_articles:
                break

            articles.extend(page_articles)

            # Tạm dừng để tránh gửi quá nhiều request
            time.sleep(1)

        return articles
        
    def get_category_url(self, category, page):
        """Lấy URL cho trang danh mục"""
        raise NotImplementedError("Subclasses must implement this method")
        
    def crawl_article_details(self, articles, max_articles=10, callback=None):
        """Crawl chi tiết các bài viết từ danh sách URL"""
        detailed_articles = []

        for i, article in enumerate(articles[:max_articles]):
            message = f"Đang crawl chi tiết bài viết {i + 1}/{min(len(articles), max_articles)}: {article['title']}"
            print(message)
            if callback:
                callback(message)

            article_detail = self.parse_article_detail(article['url'], article['category'])

            if article_detail:
                # Bỏ trường source
                detailed_articles.append(article_detail)

            # Tạm dừng để tránh gửi quá nhiều request
            time.sleep(1)

        return detailed_articles
        
    def export_to_json(self, articles, filename, callback=None):
        """Xuất dữ liệu ra file JSON"""
        if not articles:
            message = "Không có dữ liệu để xuất ra file JSON"
            print(message)
            if callback:
                callback(message)
            return False

        try:
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                # Sử dụng ensure_ascii=False để giữ nguyên ký tự Unicode
                # Thêm separators để loại bỏ khoảng trắng không cần thiết
                json.dump(articles, jsonfile, ensure_ascii=False, indent=4, separators=(',', ': '))

            message = f"Đã xuất dữ liệu ra file JSON: {filename}"
            print(message)
            if callback:
                callback(message)
            return True
        except Exception as e:
            message = f"Lỗi khi xuất dữ liệu ra file JSON: {e}"
            print(message)
            if callback:
                callback(message)
            return False


class VnExpressCrawler(NewsCrawler):
    def __init__(self):
        super().__init__()
        self.base_url = "https://vnexpress.net"
        self.source_name = "VnExpress"
        self.categories = {
            "thoi-su": 1,
            "the-gioi": 2,
            "kinh-doanh": 3,
            "giai-tri": 4,
            "the-thao": 5,
            "phap-luat": 6,
            "giao-duc": 7,
            "suc-khoe": 8,
            "doi-song": 9,
            "du-lich": 10,
            "khoa-hoc-cong-nghe": 11,
            "bat-dong-san": 12
        }
        self.category_names = {
            1: "Thời sự",
            2: "Thế giới",
            3: "Kinh doanh",
            4: "Giải trí",
            5: "Thể thao",
            6: "Pháp luật",
            7: "Giáo dục",
            8: "Sức khỏe",
            9: "Đời sống",
            10: "Du lịch",
            11: "Khoa học công nghệ",
            12: "Bất động sản"
        }
        
    def get_category_url(self, category, page):
        """Lấy URL cho trang danh mục"""
        url = f"{self.base_url}/{category}"
        if page > 1:
            url += f"-p{page}"
        return url

    def parse_article_list(self, html_content, category_id):
        """Phân tích danh sách bài viết từ trang danh mục"""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []

        # Tìm các bài viết chính
        article_items = soup.select('.item-news')
        print(f"VnExpress: Đã tìm thấy {len(article_items)} phần tử bài viết")

        for item in article_items:
            try:
                title_tag = item.select_one('.title-news a')
                if not title_tag:
                    continue

                title = title_tag.text.strip()
                url = title_tag.get('href')

                # Kiểm tra xem URL có đầy đủ domain chưa
                if url and not url.startswith('http'):
                    url = self.base_url + url

                description = ""
                desc_tag = item.select_one('.description')
                if desc_tag:
                    description = desc_tag.text.strip()

                # Cải thiện việc lấy ảnh thumbnail
                thumbnail = ""
                img_tag = item.select_one('.thumb-art img')
                if img_tag:
                    if img_tag.has_attr('data-src'):
                        thumbnail = img_tag['data-src']
                    elif img_tag.has_attr('src'):
                        thumbnail = img_tag['src']
                    
                    # Đảm bảo URL ảnh là đầy đủ
                    if thumbnail:
                        if thumbnail.startswith('//'):
                            thumbnail = 'https:' + thumbnail
                        elif not thumbnail.startswith('http'):
                            thumbnail = self.base_url + thumbnail

                articles.append({
                    'title': title,
                    'url': url,
                    'description': description,
                    'thumbnail': thumbnail,
                    'category': category_id
                })
            except Exception as e:
                print(f"Lỗi khi xử lý bài viết: {e}")
                continue

        return articles

    def parse_article_detail(self, url, category_id):
        """Phân tích chi tiết bài viết từ URL"""
        html_content = self.get_page_content(url)
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, 'html.parser')

        def clean_tag(tag):
            # Clean <p>
            if tag.name == 'p':
                for attr in list(tag.attrs):
                    del tag[attr]
            # Clean <img>
            elif tag.name == 'img':
                keep = ['src', 'alt', 'width', 'height']
                # Ưu tiên data-src nếu có
                if tag.has_attr('data-src'):
                    tag['src'] = tag['data-src']
                for attr in list(tag.attrs):
                    if attr not in keep:
                        del tag[attr]
                # Chuẩn hóa src
                if tag.has_attr('src'):
                    src = tag['src']
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif not src.startswith('http'):
                        src = self.base_url + src
                    tag['src'] = src
            # Clean <source>
            elif tag.name == 'source':
                keep = ['srcset']
                for attr in list(tag.attrs):
                    if attr not in keep:
                        del tag[attr]
                # Chuẩn hóa srcset
                if tag.has_attr('srcset'):
                    srcset = tag['srcset']
                    parts = [part.strip() for part in srcset.split(',')]
                    srcs = []
                    for part in parts:
                        url = part.split(' ')[0]
                        if url.startswith('//'):
                            url = 'https:' + url
                        elif not url.startswith('http'):
                            url = self.base_url + url
                        suffix = ' ' + ' '.join(part.split(' ')[1:]) if len(part.split(' ')) > 1 else ''
                        srcs.append(url + suffix)
                    tag['srcset'] = ', '.join(srcs)
            # Clean <picture>
            elif tag.name == 'picture':
                for attr in list(tag.attrs):
                    del tag[attr]
            # Format figcaption (căn giữa và chữ nghiêng)
            elif tag.name == 'figcaption':
                # Chỉ giữ lại description nếu có
                itemprop = tag.get('itemprop') if tag.has_attr('itemprop') else None
                for attr in list(tag.attrs):
                    del tag[attr]
                if itemprop == 'description':
                    tag['itemprop'] = itemprop
                # Thêm style để căn giữa và chữ nghiêng
                tag['style'] = 'text-align:center; font-style:italic;'
            return tag

        try:
            # Lấy tiêu đề
            title = ""
            title_tag = soup.select_one('h1.title-detail')
            if title_tag:
                title = title_tag.text.strip()
                
            # Hiển thị debug
            print(f"Tiêu đề: {title}")

            # Lấy mô tả/excerpt
            excerpt = ""
            desc_tag = soup.select_one('p.description')
            if desc_tag:
                excerpt = desc_tag.text.strip()

            # Lấy ảnh chính của bài viết trước khi xử lý nội dung
            image = ""
            # Tìm ảnh đại diện theo thứ tự ưu tiên
            # 1. Ảnh đầu tiên trong .fig-picture
            main_img = soup.select_one('.fig-picture img')
            if main_img:
                if main_img.has_attr('data-src'):
                    image = main_img['data-src']
                elif main_img.has_attr('src'):
                    image = main_img['src']

            # 2. Ảnh trong picture đầu tiên của .fig-picture
            if not image:
                main_picture = soup.select_one('.fig-picture picture')
                if main_picture:
                    img = main_picture.find('img')
                    if img:
                        if img.has_attr('data-src'):
                            image = img['data-src']
                        elif img.has_attr('src'):
                            image = img['src']

            # 3. Ảnh đại diện có thể nằm trong meta tag
            if not image:
                meta_img = soup.select_one('meta[property="og:image"]')
                if meta_img and meta_img.has_attr('content'):
                    image = meta_img['content']

            # 4. Nếu vẫn không có, thử lấy ảnh đầu tiên trong bài viết
            if not image:
                first_img = soup.select_one('.fck_detail img')
                if first_img:
                    if first_img.has_attr('data-src'):
                        image = first_img['data-src']
                    elif first_img.has_attr('src'):
                        image = first_img['src']

            # Đảm bảo URL ảnh là đầy đủ
            if image:
                if image.startswith('//'):
                    image = 'https:' + image
                elif not image.startswith('http'):
                    image = self.base_url + image

            # Lấy nội dung theo định dạng CKEditor
            content_html = ""
            content_div = soup.select_one('.fck_detail')
            if content_div:
                # Làm sạch tất cả các thẻ
                for tag in content_div.find_all(['p', 'img', 'picture', 'source', 'figcaption'], recursive=True):
                    clean_tag(tag)
                
                # Xử lý các figure > picture: lấy picture ra ngoài
                for figure in content_div.find_all('figure'):
                    picture = figure.find('picture')
                    if picture:
                        # Nếu có figcaption, chuyển thành p
                        figcaption = figure.find('figcaption')
                        if figcaption:
                            p = soup.new_tag('p')
                            p.string = figcaption.get_text()
                            p['style'] = 'text-align:center; font-style:italic;'
                            figure.insert_after(p)
                        # Đưa picture ra sau figure
                        figure.insert_after(picture)
                        # Xóa figure
                        figure.decompose()
                
                # Loại bỏ các thẻ fig-picture
                for fig_picture in content_div.select('.fig-picture'):
                    fig_picture.decompose()
                
                # Thu thập nội dung: lấy p, picture, img (không lấy figure)
                content_parts = []
                for tag in content_div.children:
                    if tag.name in ['p', 'picture', 'img']:
                        content_parts.append(str(tag))
                content_html = ''.join(content_parts)
                
                # Nếu không có excerpt, lấy đoạn đầu tiên làm excerpt
                if not excerpt and content_div:
                    first_p = content_div.find('p')
                    if first_p:
                        excerpt = first_p.text.strip()
                
                # Hiển thị debug
                print(f"Nội dung lấy được (dài {len(content_html)}): {content_html[:100]}...")
                
            # Hiển thị debug excerpt
            print(f"Tóm tắt (dài: {len(excerpt)}): {excerpt[:50]}...")

            article = {
                'title': title,
                'content': content_html,
                'excerpt': excerpt,
                'image': image,
                'category': category_id,
                'status': 'published'
            }

            return article
        except Exception as e:
            print(f"Lỗi khi phân tích bài viết {url}: {e}")
            return None


class VietnamNetCrawler(NewsCrawler):
    def __init__(self):
        super().__init__()
        self.base_url = "https://vietnamnet.vn"
        self.source_name = "VietnamNet"
        # Category IDs start from 201 to differentiate from other sources
        self.categories = {
            "thoi-su": 1,
            "the-gioi": 2,
            "kinh-doanh": 3,
            "giai-tri": 4,
            "the-thao": 5,
            "giao-duc": 7,
            "suc-khoe": 8,
            "doi-song": 9,
            "du-lich": 10,
            "cong-nghe": 11,
            "bat-dong-san": 12,
            "oto-xe-may": 13,
        }
        self.category_names = {
            1: "Thời sự",
            2: "Thế giới",
            3: "Kinh doanh",
            4: "Giải trí",
            5: "Thể thao",
            7: "Giáo dục",
            8: "Sức khỏe",
            9: "Đời sống",
            10: "Du lịch",
            11: "Công nghệ",
            12: "Bất động sản",
            13: "Ô tô - Xe máy",
        }
        
    def get_category_url(self, category, page):
        """Lấy URL cho trang danh mục"""
        if page > 1:
            url = f"{self.base_url}/{category}-page{page}"
        else:
            url = f"{self.base_url}/{category}"
        return url

    def parse_article_list(self, html_content, category_id):
        """Phân tích danh sách bài viết từ trang danh mục"""
        if not html_content:
            print("Không có nội dung HTML để phân tích")
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []

        # Tìm tất cả các link bài viết
        title_links = soup.select('h1 a, h2 a, h3 a, a.title, .title a, a.cms-link, a.link-title')
        print(f"VietnamNet: Đã tìm thấy {len(title_links)} link bài viết")
        
        # Tạo danh sách URL đã xử lý để tránh trùng lặp
        processed_urls = set()

        for title_tag in title_links:
            try:
                url = title_tag.get('href')
                
                # Bỏ qua các link không phải bài viết hoặc đã xử lý
                if not url or not url.startswith('/') or url in processed_urls:
                    continue
                    
                # Đảm bảo URL là đầy đủ
                if url.startswith('/'):
                    url = self.base_url + url
                
                processed_urls.add(url)
                
                title = title_tag.text.strip()
                if not title:
                    continue

                # Tìm mô tả và ảnh từ phần tử cha
                description = ""
                thumbnail = ""
                
                # Tìm mô tả trong các phần tử xung quanh
                parent = title_tag.parent
                for i in range(3):  # Tìm trong 3 cấp cha
                    if parent:
                        desc_tag = parent.select_one('.sapo, .lead, .description, .des')
                        if desc_tag:
                            description = desc_tag.text.strip()
                            break
                        # Di chuyển lên phần tử cha tiếp theo
                        parent = parent.parent

                # Tìm ảnh trong các phần tử xung quanh
                parent = title_tag.parent
                for i in range(3):  # Tìm trong 3 cấp cha
                    if parent:
                        img_tag = parent.select_one('img')
                        if img_tag:
                            if img_tag.has_attr('data-src'):
                                thumbnail = img_tag['data-src']
                            elif img_tag.has_attr('src'):
                                thumbnail = img_tag['src']
                            elif img_tag.has_attr('data-original'):
                                thumbnail = img_tag['data-original']
                                
                            if thumbnail:
                                break
                        # Di chuyển lên phần tử cha tiếp theo
                        parent = parent.parent
                
                # Đảm bảo URL ảnh là đầy đủ
                if thumbnail:
                    if thumbnail.startswith('//'):
                        thumbnail = 'https:' + thumbnail
                    elif not thumbnail.startswith('http'):
                        thumbnail = self.base_url + thumbnail

                articles.append({
                    'title': title,
                    'url': url,
                    'description': description,
                    'thumbnail': thumbnail,
                    'category': category_id
                })
            except Exception as e:
                print(f"Lỗi khi xử lý bài viết: {e}")
                continue

        return articles

    def parse_article_detail(self, url, category_id):
        """Phân tích chi tiết bài viết từ URL"""
        html_content = self.get_page_content(url)
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, 'html.parser')

        def clean_tag(tag):
            # Clean <p>
            if tag.name == 'p':
                for attr in list(tag.attrs):
                    del tag[attr]
            # Clean <img>
            elif tag.name == 'img':
                keep = ['src', 'alt', 'width', 'height']
                # Ưu tiên data-src nếu có
                if tag.has_attr('data-src'):
                    tag['src'] = tag['data-src']
                elif tag.has_attr('data-original'):
                    tag['src'] = tag['data-original']
                for attr in list(tag.attrs):
                    if attr not in keep:
                        del tag[attr]
                # Chuẩn hóa src
                if tag.has_attr('src'):
                    src = tag['src']
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif not src.startswith('http'):
                        src = self.base_url + src
                    tag['src'] = src
            # Clean <figure>
            elif tag.name == 'figure':
                for attr in list(tag.attrs):
                    del tag[attr]
            # Format figcaption
            elif tag.name == 'figcaption':
                for attr in list(tag.attrs):
                    del tag[attr]
                # Thêm style để căn giữa và chữ nghiêng
                tag['style'] = 'text-align:center; font-style:italic;'
            return tag

        try:
            # Lấy tiêu đề
            title = ""
            title_tag = soup.select_one('h1.title, h1.cms-title, h1.ArticleDetail, .detail-title h1, .content-detail h1')
            if title_tag:
                title = title_tag.text.strip()
            else:
                # Tìm thẻ h1 đầu tiên nếu không có title cụ thể
                h1_tag = soup.find('h1')
                if h1_tag:
                    title = h1_tag.text.strip()
                    
            # Hiển thị debug
            print(f"Tiêu đề: {title}")

            # Lấy ảnh chính của bài viết
            image = ""
            # Tìm ảnh đại diện từ meta tag
            meta_img = soup.select_one('meta[property="og:image"]')
            if meta_img and meta_img.has_attr('content'):
                image = meta_img['content']

            # Lấy nội dung
            content_html = ""
            # Tìm div chứa nội dung chính - ưu tiên maincontent
            content_div = soup.select_one('div.maincontent, div#maincontent, .content-detail__content, .ArticleContent, .cms-body, .detail-content, .article-body')
            if content_div:
                # Làm sạch các thẻ
                for tag in content_div.find_all(['p', 'img', 'figure', 'figcaption'], recursive=True):
                    clean_tag(tag)
                
                # Loại bỏ các phần không cần thiết
                for div in content_div.select('.VnnAdsBox, .ImageBox, .article__ads, .box-banner, .ads, .insert-wiki-content, .ck-cms-insert-neww-group'):
                    div.decompose()
                
                # Thu thập nội dung: lấy p, figure, img
                content_parts = []
                for tag in content_div.find_all(['p', 'figure']):
                    content_parts.append(str(tag))
                content_html = ''.join(content_parts)
                
                # Hiển thị debug
                print(f"Nội dung lấy được (dài {len(content_html)}): {content_html[:100]}...")

            # Lấy excerpt từ đoạn văn đầu tiên nếu không có sẵn excerpt
            excerpt = ""
            desc_tag = soup.select_one('.article-relate__summary, .content-detail__summary, .ArticleLead, .cms-desc, .article-body .sapo, .detail-article .sapo')
            if desc_tag:
                excerpt = desc_tag.text.strip()
            
            # Nếu không tìm thấy excerpt, lấy từ đoạn đầu tiên của nội dung
            if not excerpt and content_div:
                first_p = content_div.find('p')
                if first_p:
                    excerpt = first_p.text.strip()
            
            # Hiển thị debug
            print(f"Tóm tắt (dài: {len(excerpt)}): {excerpt[:50]}...")

            article = {
                'title': title,
                'content': content_html,
                'excerpt': excerpt,
                'image': image,
                'category': category_id,
                'status': 'published'
            }

            return article
        except Exception as e:
            print(f"Lỗi khi phân tích bài viết {url}: {e}")
            return None


class CrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("News Crawler")
        self.root.geometry("800x600")

        # Khởi tạo các crawler
        self.crawlers = {
            "VnExpress": VnExpressCrawler(),
            "VietnamNet": VietnamNetCrawler()
        }
        self.current_crawler = self.crawlers["VnExpress"]
        self.setup_ui()

    def setup_ui(self):
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Tiêu đề
        title_label = ttk.Label(main_frame, text="News Crawler", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)

        # Frame cấu hình
        config_frame = ttk.LabelFrame(main_frame, text="Cấu hình Crawler", padding="10")
        config_frame.pack(fill=tk.X, pady=10)

        # Chọn nguồn
        source_frame = ttk.Frame(config_frame)
        source_frame.pack(fill=tk.X, pady=5)

        ttk.Label(source_frame, text="Nguồn:").pack(side=tk.LEFT, padx=5)

        self.source_var = tk.StringVar(value="VnExpress")
        self.source_combobox = ttk.Combobox(source_frame, textvariable=self.source_var, width=20)
        self.source_combobox['values'] = list(self.crawlers.keys())
        self.source_combobox.pack(side=tk.LEFT, padx=5)
        self.source_combobox.bind("<<ComboboxSelected>>", self.update_categories)

        # Chọn danh mục
        category_frame = ttk.Frame(config_frame)
        category_frame.pack(fill=tk.X, pady=5)

        ttk.Label(category_frame, text="Danh mục:").pack(side=tk.LEFT, padx=5)

        self.category_var = tk.StringVar()
        self.category_combobox = ttk.Combobox(category_frame, textvariable=self.category_var, width=30)
        self.category_combobox.pack(side=tk.LEFT, padx=5)

        # Số trang và số bài viết
        pages_frame = ttk.Frame(config_frame)
        pages_frame.pack(fill=tk.X, pady=5)

        ttk.Label(pages_frame, text="Số trang:").pack(side=tk.LEFT, padx=5)
        self.pages_var = tk.StringVar(value="2")
        pages_entry = ttk.Entry(pages_frame, textvariable=self.pages_var, width=5)
        pages_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(pages_frame, text="Số bài viết:").pack(side=tk.LEFT, padx=5)
        self.articles_var = tk.StringVar(value="10")
        articles_entry = ttk.Entry(pages_frame, textvariable=self.articles_var, width=5)
        articles_entry.pack(side=tk.LEFT, padx=5)

        # Thư mục xuất
        output_frame = ttk.Frame(config_frame)
        output_frame.pack(fill=tk.X, pady=5)

        ttk.Label(output_frame, text="Thư mục xuất:").pack(side=tk.LEFT, padx=5)
        self.output_var = tk.StringVar(value="news_data")
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var, width=30)
        output_entry.pack(side=tk.LEFT, padx=5)

        # Nút crawl
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.crawl_button = ttk.Button(button_frame, text="Bắt đầu Crawl", command=self.start_crawling)
        self.crawl_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Dừng", command=self.stop_crawling, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Khu vực log
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Thanh trạng thái
        self.status_var = tk.StringVar(value="Sẵn sàng")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

        # Biến để kiểm soát luồng
        self.crawling = False
        
        # Cập nhật danh sách danh mục ban đầu
        self.update_categories()

    def update_categories(self, event=None):
        """Cập nhật danh sách danh mục khi thay đổi nguồn"""
        source = self.source_var.get()
        self.current_crawler = self.crawlers[source]
        
        # Cập nhật combobox danh mục
        categories = [f"{id}. {name}" for id, name in self.current_crawler.category_names.items()]
        self.category_combobox['values'] = categories
        if categories:
            self.category_combobox.current(0)

    def log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.status_var.set(message)
        self.root.update_idletasks()

    def start_crawling(self):
        if self.crawling:
            return

        # Lấy thông tin cấu hình
        source = self.source_var.get()
        self.current_crawler = self.crawlers[source]
        
        category_selection = self.category_var.get()
        if not category_selection:
            messagebox.showerror("Lỗi", "Vui lòng chọn danh mục")
            return
        
        category_id = int(category_selection.split('.')[0])
        category_key = next((k for k, v in self.current_crawler.categories.items() if v == category_id), None)

        if not category_key:
            messagebox.showerror("Lỗi", "Danh mục không hợp lệ")
            return

        try:
            num_pages = int(self.pages_var.get())
            max_articles = int(self.articles_var.get())
            output_dir = self.output_var.get()
        except ValueError:
            messagebox.showerror("Lỗi", "Số trang và số bài viết phải là số nguyên")
            return

        # Tạo thư mục xuất nếu chưa tồn tại
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Cập nhật UI
        self.crawl_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

        # Bắt đầu crawl trong một luồng riêng
        self.crawling = True
        threading.Thread(target=self.crawl_process, args=(category_key, num_pages, max_articles, output_dir, source),
                         daemon=True).start()

    def crawl_process(self, category_key, num_pages, max_articles, output_dir, source):
        try:
            crawler = self.crawlers[source]
            self.log(f"Bắt đầu crawl nguồn: {source}, danh mục: {crawler.category_names[crawler.categories[category_key]]}")

            # Crawl danh sách bài viết
            articles = crawler.crawl_category(category_key, num_pages, self.log)

            if not self.crawling:
                self.log("Đã dừng crawl theo yêu cầu")
                self.finish_crawling()
                return

            self.log(f"Đã tìm thấy {len(articles)} bài viết")

            if not articles:
                self.log("Không tìm thấy bài viết nào. Kết thúc chương trình.")
                self.finish_crawling()
                return

            # Crawl chi tiết bài viết
            self.log(f"Đang crawl chi tiết {min(max_articles, len(articles))} bài viết...")
            detailed_articles = crawler.crawl_article_details(articles, max_articles, self.log)

            if not self.crawling:
                self.log("Đã dừng crawl theo yêu cầu")
                self.finish_crawling()
                return

            # Tạo tên file với timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = os.path.join(output_dir, f"{source.lower()}_{category_key}_{timestamp}.json")

            # Xuất dữ liệu ra file
            crawler.export_to_json(detailed_articles, json_filename, self.log)

            self.log("\nQuá trình crawl dữ liệu đã hoàn tất!")
            self.log(f"Số bài viết đã crawl: {len(detailed_articles)}")
            self.log(f"Dữ liệu đã được lưu vào: {json_filename}")

        except Exception as e:
            self.log(f"Lỗi: {str(e)}")
        finally:
            self.finish_crawling()

    def stop_crawling(self):
        self.crawling = False
        self.log("Đang dừng crawl...")

    def finish_crawling(self):
        self.crawling = False
        self.root.after(0, lambda: self.crawl_button.configure(state=tk.NORMAL))
        self.root.after(0, lambda: self.stop_button.configure(state=tk.DISABLED))
        self.root.after(0, lambda: self.status_var.set("Sẵn sàng"))


if __name__ == "__main__":
    root = tk.Tk()
    app = CrawlerGUI(root)
    root.mainloop()