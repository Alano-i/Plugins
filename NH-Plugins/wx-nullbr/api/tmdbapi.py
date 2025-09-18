import httpx
import logging

logger = logging.getLogger(__name__)

class TmdbApi:
    def __init__(self):
        self.base_url = "https://api.themoviedb.org/3"
        self.api_key = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3ZjFkODYxYWUxMTNjN2NjZGQ2YTM4NGNiMjlmYmFjMiIsIm5iZiI6MTY0NDkwNjE2OS45MzEsInN1YiI6IjYyMGI0NmI5YzA3MmEyMDA2OGE2ZjgyZCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.lmCVbPJA7ddKpGfGVZ02Gth_3bTGOJczaQek9tWWZOY"

    def get_movie_info(self, movie_name):
        url = f"{self.base_url}/search/movie?query={movie_name}&include_adult=false&language=zh-CN&page=1"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        try:
            response = httpx.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                logger.warning("TMDB 响应非字典结构: %s", type(data))
                return {"results": []}
            return data
        except httpx.TimeoutException as e:
            logger.warning("TMDB 请求超时: %s", e)
            return {"results": []}
        except httpx.HTTPStatusError as e:
            logger.warning("TMDB HTTP 状态异常: %s", e)
            return {"results": []}
        except httpx.RequestError as e:
            logger.warning("TMDB 网络请求异常: %s", e)
            return {"results": []}
        except ValueError as e:
            logger.warning("TMDB JSON 解析失败: %s", e)
            return {"results": []}
    
    def get_series_info(self, series_name):
        url = f"{self.base_url}/search/tv?query={series_name}&include_adult=false&language=zh-CN&page=1"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        try:
            response = httpx.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                logger.warning("TMDB 响应非字典结构: %s", type(data))
                return {"results": []}
            return data
        except httpx.TimeoutException as e:
            logger.warning("TMDB 请求超时: %s", e)
            return {"results": []}
        except httpx.HTTPStatusError as e:
            logger.warning("TMDB HTTP 状态异常: %s", e)
            return {"results": []}
        except httpx.RequestError as e:
            logger.warning("TMDB 网络请求异常: %s", e)
            return {"results": []}
        except ValueError as e:
            logger.warning("TMDB JSON 解析失败: %s", e)
            return {"results": []}
    
    def get_backdrop_url(self, backdrop_path):
        return f"https://image.tmdb.org/t/p/original{backdrop_path}"
    

    def _parse_movie_detail(self, movie_detail):
        result = []
        for i in movie_detail:
            title = i.get("title")
            backdrop_path = i.get("backdrop_path", None)
            tmdb_id = i.get("id")
            overview = i.get("overview", None)
            release_date = i.get("release_date", "")
            release_year = release_date.split("-")[0]
            rating = i.get("vote_average", 0)
            genres = i.get("genre_ids", [])
            result.append({
                "type": "movie",
                "title": title,
                "backdrop_path": backdrop_path,
                "tmdb_id": tmdb_id,
                "overview": overview,
                "release_year": release_year,
                "rating": rating,
                "genres": genres
            })
        return result

    def _parse_series_detail(self, series_detail):
        result = []
        for i in series_detail:
            title = i.get("name")
            backdrop_path = i.get("backdrop_path", None)
            tmdb_id = i.get("id")
            overview = i.get("overview", None)
            first_air_date = i.get("first_air_date", "")
            release_year = first_air_date.split("-")[0]
            rating = i.get("vote_average", 0)
            genres = i.get("genre_ids", [])
            result.append({
                "type": "tv",
                "title": title,
                "backdrop_path": backdrop_path,
                "tmdb_id": tmdb_id,
                "overview": overview,
                "release_year": release_year,
                "rating": rating,
                "genres": genres
            })
        return result
    
    def search_by_keyword(self, keyword):
        movie_detail = self.get_movie_info(keyword).get("results") or []
        series_detail = self.get_series_info(keyword).get("results") or []
        result = self._parse_movie_detail(movie_detail) + self._parse_series_detail(series_detail)
        def sort_key(item):
            backdrop_path = item.get("backdrop_path")
            release_year = item.get("release_year")
            rating = item.get("rating", 0)
            has_required_fields = 1 if (backdrop_path and release_year and str(release_year).isdigit()) else 0
            try:
                year_val = int(release_year) if release_year and str(release_year).isdigit() else -1
            except (TypeError, ValueError):
                year_val = -1
            try:
                rating_val = float(rating)
            except (TypeError, ValueError):
                rating_val = -1.0
            # 先按是否具备必要字段，其次按年份，再按评分，全部倒序
            return (has_required_fields, rating_val, year_val)

        result.sort(key=sort_key, reverse=True)

        return result

tmdb = TmdbApi()