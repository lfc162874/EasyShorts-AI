import { IsString, IsOptional, IsInt, IsBoolean, IsEnum, MaxLength } from 'class-validator';
import { Type } from 'class-transformer';
import { MenuType } from '../../common/constants/enums';

export class CreateMenuDto {
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  parent_id?: number | null;

  @IsString()
  @MaxLength(128)
  name!: string;

  @IsString()
  @MaxLength(128)
  title!: string;

  @IsOptional()
  @IsString()
  @MaxLength(255)
  path?: string;

  @IsOptional()
  @IsString()
  @MaxLength(255)
  component?: string;

  @IsOptional()
  @IsString()
  @MaxLength(64)
  icon?: string;

  @IsOptional()
  @IsString()
  @MaxLength(128)
  permission_code?: string;

  @IsEnum(MenuType)
  menu_type: MenuType = MenuType.MENU;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  sort_order?: number = 0;

  @IsOptional()
  @IsBoolean()
  hidden?: boolean = false;
}
