import { IsOptional, IsInt, Min, Max } from 'class-validator';
import { Type } from 'class-transformer';

export class PaginationDto {
  @Type(() => Number)
  @IsOptional()
  @IsInt()
  @Min(1)
  page?: number = 1;

  @Type(() => Number)
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(100)
  page_size?: number = 20;

  @IsOptional()
  keyword?: string;
}
