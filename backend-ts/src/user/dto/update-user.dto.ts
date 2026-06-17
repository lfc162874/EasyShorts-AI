import { IsOptional } from 'class-validator';
import { PartialType, OmitType } from '@nestjs/swagger';
import { CreateUserDto } from './create-user.dto';

// 所有字段变为可选，用于更新
export class UpdateUserDto extends PartialType(
  OmitType(CreateUserDto, ['password'] as const),
) {
  @IsOptional()
  password?: string;
}
