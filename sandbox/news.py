from pydantic import BaseModel, Field
import json


class News(BaseModel):

    class NewsItem(BaseModel):
        title: str = Field(..., description="The title of the news item")
        content: str = Field(..., description="The content of the news item")
        url: str = Field("", description="The URL of the news item")
        origin: str = Field(..., description="The origin/source name of the news item")

        class Metrics(BaseModel):
            views: int = Field(..., description="Number of views for the news item")
            likes: int = Field(..., description="Number of likes for the news item")
            comments: int = Field(
                ..., description="Number of comments on the news item"
            )
            reposts: int = Field(..., description="Number of reposts of the news item")
            freshness: float = Field(
                ...,
                description="Time in seconds passed since the news item was published",
            )

            class CompetitorsEngagement(BaseModel):
                comp_one: bool = Field(
                    False, description="Engagement status for competitor one"
                )
                comp_two: bool = Field(
                    False, description="Engagement status for competitor two"
                )

            competitors: CompetitorsEngagement = Field(
                ..., description="Engagement status for competitors"
            )

        metrics: Metrics = Field(
            ..., description="Engagement metrics for the news item"
        )

    news: list[NewsItem] = Field(..., description="List of news items")


if __name__ == "__main__":

    schema = News.model_json_schema()
    json.dump(schema, open("sandbox/schema.json", "w"), indent=2)
