from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://gis_user:gis_pass@localhost:5432/fleet_tracking"

    sim_vehicle_count: int = 12
    sim_tick_seconds: float = 1.0
    # min_lon,min_lat,max_lon,max_lat - default: downtown San Francisco
    sim_city_bbox: str = "-122.4294,37.7599,-122.3959,37.7899"

    position_retention_hours: int = 24
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        min_lon, min_lat, max_lon, max_lat = (float(v) for v in self.sim_city_bbox.split(","))
        return min_lon, min_lat, max_lon, max_lat

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
